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
import time
from dataclasses import dataclass

import redis

from safety.guardian.engine import (
    GuardianEngine,
    RuleAction,
    get_guardian_engine,
)
from safety.guardian.engine import (
    Severity as GuardianSeverity,
)
from safety.observability.canary import safety_canary
from safety.observability.logging_setup import get_logger
from safety.observability.metrics import PRECHECK_LATENCY, REFUSALS_TOTAL
from safety.observability.security_monitoring import (
    SecurityEvent,
    SecurityEventSeverity,
    SecurityEventType,
    security_logger,
)

logger = get_logger("detectors.pre_check")

# ---------------------------------------------------------------------------
# Redis client for dynamic blocklist (sync client — pre-check is sync)
# ---------------------------------------------------------------------------
_redis_client: redis.Redis | None = None
_redis_unavailable: bool = False


# ---------------------------------------------------------------------------
# Guardian engine helpers
# ---------------------------------------------------------------------------
def _guardian_reason_code(rule_id: str, category: str | None = None) -> str:
    """Derive backward-compatible reason code from guardian rule.

    Uses the rule's *category* (e.g. ``high_risk_weapon``, ``csam_block``)
    which maps 1-to-1 to the legacy reason codes expected by downstream
    consumers.  Falls back to ``rule_id.upper()`` when no category is set.
    """
    source = category or rule_id
    return source.upper()


def _get_guardian() -> GuardianEngine:
    """Get guardian engine, loading rules on first use if needed."""
    engine = get_guardian_engine()
    if not engine.registry.get_all():
        from safety.guardian.loader import get_rule_loader

        rules = get_rule_loader().load_all_rules()
        engine.load_rules(rules)
    return engine


def _get_redis() -> redis.Redis | None:
    global _redis_client, _redis_unavailable
    if _redis_unavailable:
        return None
    if _redis_client is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis_client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=0.5)
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
        _dynamic_blocklist = {m.lower() for m in members} if members else set()  # type: ignore[reportAssignmentIssue]
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
@dataclass(frozen=True)
class PreCheckResult:
    """Result of a pre-check evaluation."""

    blocked: bool
    reason_code: str | None = None


def quick_block(text: str) -> PreCheckResult:
    """
    Synchronous pre-check. Returns PreCheckResult.

    MUST stay under 50ms. No network calls, no ML inference.
    """
    start = time.monotonic()
    try:
        if not text or not text.strip():
            return PreCheckResult(blocked=False)

        # 1. Length check
        if len(text) > _MAX_INPUT_LENGTH:
            REFUSALS_TOTAL.labels(reason_code="INPUT_TOO_LONG").inc()
            return PreCheckResult(blocked=True, reason_code="INPUT_TOO_LONG")

        normalized = text.strip()

        # 2. Unified rule engine patterns (Project GUARDIAN)
        engine = _get_guardian()
        matches, _latency = engine.evaluate(normalized, use_cache=True)

        # Find the first blocking match (same logic as quick_check but with
        # backward-compatible reason codes derived from rule IDs).
        for m in matches:
            is_block = m.action in (RuleAction.BLOCK, RuleAction.CANARY) or (
                m.action == RuleAction.ESCALATE and m.severity in (GuardianSeverity.HIGH, GuardianSeverity.CRITICAL)
            )
            if not is_block:
                continue

            reason_code = _guardian_reason_code(m.rule_id, category=m.category)
            REFUSALS_TOTAL.labels(reason_code=reason_code).inc()

            security_logger.log_event(
                SecurityEvent(
                    event_id=f"det-{int(time.time())}-{m.rule_id}",
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    event_type=SecurityEventType.AI_INPUT_BLOCKED,
                    severity=SecurityEventSeverity(m.severity.value),
                    source="detectors.pre_check",
                    user_id=None,
                    ip_address=None,
                    session_id=None,
                    details={
                        "rule_id": m.rule_id,
                        "rule_name": m.rule_name,
                        "reason_code": reason_code,
                        "input_length": len(normalized),
                    },
                    risk_score=0.8 if m.severity in (GuardianSeverity.HIGH, GuardianSeverity.CRITICAL) else 0.5,
                )
            )

            return PreCheckResult(blocked=True, reason_code=reason_code)

        # 3. Dynamic blocklist (cached)
        _refresh_blocklist()
        normalized_lower = normalized.lower()
        for blocked_term in _dynamic_blocklist:
            if blocked_term in normalized_lower:
                REFUSALS_TOTAL.labels(reason_code="DYNAMIC_BLOCKLIST").inc()
                return PreCheckResult(blocked=True, reason_code="DYNAMIC_BLOCKLIST")

        # 4. Safety Canary Detection (Project GUARDIAN)
        if safety_canary.has_canary(normalized):
            REFUSALS_TOTAL.labels(reason_code="SAFETY_CANARY_DETECTED").inc()
            security_logger.log_event(
                SecurityEvent(
                    event_id=f"det-{int(time.time())}-canary",
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    event_type=SecurityEventType.PROMPT_INJECTION_ATTEMPT,  # type: ignore[reportUnknownVariableType]
                    severity=SecurityEventSeverity.CRITICAL,  # type: ignore[reportUnknownMemberType]
                    source="detectors.pre_check.canary",
                    user_id=None,
                    ip_address=None,
                    session_id=None,
                    details={
                        "reason_code": "SAFETY_CANARY_DETECTED",
                        "description": "Adversarial recycling of AI response detected via canary watermark",
                    },
                    risk_score=1.0,  # Immediate max risk
                )
            )
            return PreCheckResult(blocked=True, reason_code="SAFETY_CANARY_DETECTED")

        # TODO: Entropy check can false-positive on base64-encoded images or
        #       legitimate encoded content. Add content-type awareness.
        # 5. Entropy heuristic (detect obfuscated / encoded payloads)
        if len(normalized) > 200:
            entropy = _shannon_entropy(normalized)
            if entropy > _HIGH_ENTROPY_THRESHOLD:
                REFUSALS_TOTAL.labels(reason_code="HIGH_ENTROPY_PAYLOAD").inc()
                return PreCheckResult(blocked=True, reason_code="HIGH_ENTROPY_PAYLOAD")

        return PreCheckResult(blocked=False)

    finally:
        elapsed = time.monotonic() - start
        PRECHECK_LATENCY.observe(elapsed)
        if elapsed > 0.05:
            logger.warning(
                "precheck_exceeded_budget",
                elapsed_ms=round(elapsed * 1000, 2),
            )
