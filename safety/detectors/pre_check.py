"""
Synchronous pre-check detector. MUST complete in <50ms.

Deterministic pattern matching only — no ML, no network calls.
Returns (blocked: bool, reason_code: str | None).

Blocklist is loaded from Redis at startup and cached in-process.
Dynamic updates are picked up via periodic refresh (not per-request).
"""

from __future__ import annotations

import math
import os
import re
import time
from typing import ClassVar

import redis

from safety.observability.canary import safety_canary
from safety.observability.logging_setup import get_logger
from safety.observability.metrics import PRECHECK_LATENCY, REFUSALS_TOTAL
from safety.observability.security_monitoring import SecurityEvent, security_logger
from safety.rules.engine import get_rule_engine

logger = get_logger("detectors.pre_check")

# ---------------------------------------------------------------------------
# Redis client for dynamic blocklist (sync client — pre-check is sync)
# ---------------------------------------------------------------------------
_redis_client: redis.Redis | None = None
_redis_unavailable: bool = False

# Unified rule engine
_rule_engine = get_rule_engine()
_rule_engine.load_rules()  # Load default rules


def _get_redis() -> redis.Redis | None:
    global _redis_client, _redis_unavailable
    if _redis_unavailable:
        return None
    if _redis_client is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis_client = redis.Redis.from_url(
            url, decode_responses=True, socket_connect_timeout=0.5
        )
        # Quick connectivity check
        try:
            _redis_client.ping()
        except Exception:
            _redis_unavailable = True
            _redis_client = None
            return None
    return _redis_client



# ---------------------------------------------------------------------------
# Dynamic blocklist (cached from Redis set "dynamic_blocklist")
# ---------------------------------------------------------------------------
_dynamic_blocklist: set[str] = set()
_blocklist_last_refresh: float = 0.0
_BLOCKLIST_REFRESH_INTERVAL = 60.0  # seconds


def _refresh_blocklist() -> None:
    """Refresh the in-memory dynamic blocklist from Redis."""
    global _dynamic_blocklist, _blocklist_last_refresh
    now = time.monotonic()
    if now - _blocklist_last_refresh < _BLOCKLIST_REFRESH_INTERVAL:
        return
    try:
        client = _get_redis()
        if client is None:
            return  # Redis unavailable; keep stale cache
        members = client.smembers("dynamic_blocklist")
        _dynamic_blocklist = {m.lower() for m in members} if members else set()
        _blocklist_last_refresh = now
    except Exception as exc:
        # If Redis is down, keep the stale cache; do not clear it.
        logger.warning("dynamic_blocklist_refresh_failed", error=str(exc))


# ---------------------------------------------------------------------------
# Entropy / length heuristics
# ---------------------------------------------------------------------------
_MAX_INPUT_LENGTH = 50_000  # characters
_HIGH_ENTROPY_THRESHOLD = 5.5  # bits per character (normal English ~4.0)


def _shannon_entropy(text: str) -> float:
    """Compute Shannon entropy in bits per character."""
    if not text:
        return 0.0
    freq: dict[str, int] = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(text)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def quick_block(text: str) -> tuple[bool, str | None]:
    """
    Synchronous pre-check. Returns (blocked, reason_code).

    MUST stay under 50ms. No network calls, no ML inference.
    """
    start = time.monotonic()
    try:
        if not text or not text.strip():
            return False, None

        # 1. Length check
        if len(text) > _MAX_INPUT_LENGTH:
            REFUSALS_TOTAL.labels(reason_code="INPUT_TOO_LONG").inc()
            return True, "INPUT_TOO_LONG"

        normalized = text.strip()

        # 2. Unified rule engine patterns (Project GUARDIAN)
        blocked, reason, matched_rule = _rule_engine.evaluate(normalized)
        if blocked and matched_rule:
            REFUSALS_TOTAL.labels(reason_code=reason).inc()
            
            # Log rich security event for the matched rule
            security_logger.log_event(SecurityEvent(
                event_id=f"det-{int(time.time())}-{matched_rule.id}",
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                event_type=matched_rule.event_type,
                severity=matched_rule.severity,
                source="detectors.pre_check",
                user_id=None,
                ip_address=None,
                session_id=None,
                details={
                    "rule_id": matched_rule.id,
                    "rule_name": matched_rule.name,
                    "reason_code": reason,
                    "input_length": len(normalized)
                },
                risk_score=0.8 if matched_rule.severity.value == "high" else 0.5
            ))
            
            return True, reason

        # 3. Dynamic blocklist (cached)
        _refresh_blocklist()
        normalized_lower = normalized.lower()
        for blocked_term in _dynamic_blocklist:
            if blocked_term in normalized_lower:
                REFUSALS_TOTAL.labels(reason_code="DYNAMIC_BLOCKLIST").inc()
                return True, "DYNAMIC_BLOCKLIST"

        # 4. Safety Canary Detection (Project GUARDIAN)
        if safety_canary.has_canary(normalized):
            REFUSALS_TOTAL.labels(reason_code="SAFETY_CANARY_DETECTED").inc()
            security_logger.log_event(SecurityEvent(
                event_id=f"det-{int(time.time())}-canary",
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                event_type=SecurityEventType.PROMPT_INJECTION_ATTEMPT,
                severity=SecurityEventSeverity.CRITICAL,
                source="detectors.pre_check.canary",
                user_id=None,
                ip_address=None,
                session_id=None,
                details={
                    "reason_code": "SAFETY_CANARY_DETECTED",
                    "description": "Adversarial recycling of AI response detected via canary watermark"
                },
                risk_score=1.0 # Immediate max risk
            ))
            return True, "SAFETY_CANARY_DETECTED"

        # TODO: Entropy check can false-positive on base64-encoded images or
        #       legitimate encoded content. Add content-type awareness.
        # 5. Entropy heuristic (detect obfuscated / encoded payloads)
        if len(normalized) > 200:
            entropy = _shannon_entropy(normalized)
            if entropy > _HIGH_ENTROPY_THRESHOLD:
                REFUSALS_TOTAL.labels(reason_code="HIGH_ENTROPY_PAYLOAD").inc()
                return True, "HIGH_ENTROPY_PAYLOAD"

        return False, None

    finally:
        elapsed = time.monotonic() - start
        PRECHECK_LATENCY.observe(elapsed)
        if elapsed > 0.05:
            logger.warning(
                "precheck_exceeded_budget",
                elapsed_ms=round(elapsed * 1000, 2),
            )
