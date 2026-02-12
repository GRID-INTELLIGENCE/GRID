"""
GUARDIAN-Enhanced Pre-Check Detector
Project GUARDIAN: Phase 1 - Refactored Pre-Check

Synchronous pre-check detector using the unified GUARDIAN rule engine.
MUST complete in <50ms.

Key improvements:
- Uses GUARDIAN's hybrid Trie+RegexSet engine for blazing speed
- Dynamic rule loading from unified registry
- Result caching for repeated inputs
- Better entropy detection
"""

from __future__ import annotations

import math
import os
import time
from typing import Optional, Tuple

from safety.observability.logging_setup import get_logger
from safety.observability.metrics import PRECHECK_LATENCY, REFUSALS_TOTAL

# Import GUARDIAN
from safety.guardian import (
    GuardianEngine,
    RuleAction,
    Severity,
    get_guardian_engine,
    init_guardian_rules,
)

logger = get_logger("detectors.pre_check")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_MAX_INPUT_LENGTH = int(os.getenv("GUARDIAN_MAX_INPUT_LENGTH", "50000"))
_HIGH_ENTROPY_THRESHOLD = float(os.getenv("GUARDIAN_HIGH_ENTROPY_THRESHOLD", "5.5"))
_MIN_INPUT_LENGTH_FOR_ENTROPY = int(os.getenv("GUARDIAN_MIN_ENTROPY_LENGTH", "200"))


# ---------------------------------------------------------------------------
# Entropy calculation
# ---------------------------------------------------------------------------
def _shannon_entropy(text: str) -> float:
    """Compute Shannon entropy in bits per character."""
    if not text:
        return 0.0

    freq = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1

    length = len(text)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


# ---------------------------------------------------------------------------
# GUARDIAN Integration
# ---------------------------------------------------------------------------
_guardian_initialized = False


def _ensure_guardian() -> GuardianEngine:
    """Ensure GUARDIAN is initialized."""
    global _guardian_initialized

    if not _guardian_initialized:
        engine = init_guardian_rules(auto_reload=True)
        _guardian_initialized = True
        logger.info("GUARDIAN initialized for pre-check")
        return engine

    return get_guardian_engine()


# ---------------------------------------------------------------------------
# Legacy Compatibility
# ---------------------------------------------------------------------------
def _legacy_pattern_match(text: str) -> Tuple[bool, Optional[str]]:
    """
    Legacy pattern matching for backwards compatibility.
    Uses GUARDIAN's quick_check for speed.
    """
    engine = _ensure_guardian()
    should_block, reason_code, action = engine.quick_check(text)

    if should_block and reason_code:
        return True, reason_code

    return False, None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def quick_block(text: str) -> Tuple[bool, Optional[str]]:
    """
    Synchronous pre-check using GUARDIAN engine.
    Returns (blocked, reason_code).

    MUST stay under 50ms. No network calls, no ML inference.

    Performance characteristics:
    - Trie matching: O(n + m) where n=text length, m=total keyword length
    - Regex matching: O(n * k) where k=number of patterns
    - Cache lookup: O(1)
    - Entropy calc: O(n)

    Typical latency: 1-10ms for normal inputs, <50ms worst case.
    """
    start = time.monotonic()

    try:
        # 0. Empty check
        if not text or not text.strip():
            return False, None

        normalized = text.strip()

        # 1. Length check (fast path)
        if len(normalized) > _MAX_INPUT_LENGTH:
            REFUSALS_TOTAL.labels(reason_code="INPUT_TOO_LONG").inc()
            elapsed = time.monotonic() - start
            PRECHECK_LATENCY.observe(elapsed)
            return True, "INPUT_TOO_LONG"

        # 2. GUARDIAN evaluation (unified rule engine)
        engine = _ensure_guardian()
        matches, eval_latency = engine.evaluate(normalized, use_cache=True)

        # Check for blocking matches
        for match in matches:
            if match.action in (RuleAction.BLOCK, RuleAction.CANARY):
                REFUSALS_TOTAL.labels(reason_code=match.rule_id).inc()
                elapsed = time.monotonic() - start
                PRECHECK_LATENCY.observe(elapsed)

                logger.info(
                    "guardian_block",
                    rule_id=match.rule_id,
                    category=match.category,
                    severity=match.severity.value,
                    latency_ms=eval_latency,
                )
                return True, match.rule_id.upper()

            elif match.action == RuleAction.ESCALATE and match.severity in (Severity.HIGH, Severity.CRITICAL):
                REFUSALS_TOTAL.labels(reason_code=f"ESCALATE_{match.rule_id}").inc()
                elapsed = time.monotonic() - start
                PRECHECK_LATENCY.observe(elapsed)

                logger.info(
                    "guardian_escalate",
                    rule_id=match.rule_id,
                    category=match.category,
                    latency_ms=eval_latency,
                )
                return True, f"ESCALATE_{match.category.upper()}"

        # 3. Entropy heuristic (detect obfuscated / encoded payloads)
        if len(normalized) > _MIN_INPUT_LENGTH_FOR_ENTROPY:
            entropy = _shannon_entropy(normalized)
            if entropy > _HIGH_ENTROPY_THRESHOLD:
                REFUSALS_TOTAL.labels(reason_code="HIGH_ENTROPY_PAYLOAD").inc()
                elapsed = time.monotonic() - start
                PRECHECK_LATENCY.observe(elapsed)

                logger.info(
                    "high_entropy_detected",
                    entropy=entropy,
                    threshold=_HIGH_ENTROPY_THRESHOLD,
                    text_length=len(normalized),
                )
                return True, "HIGH_ENTROPY_PAYLOAD"

        # 4. Passed all checks
        elapsed = time.monotonic() - start
        PRECHECK_LATENCY.observe(elapsed)

        if elapsed > 0.05:
            logger.warning(
                "precheck_exceeded_budget",
                elapsed_ms=round(elapsed * 1000, 2),
                text_length=len(normalized),
            )

        return False, None

    except Exception as exc:
        # Fail closed: if detector errors, refuse
        elapsed = time.monotonic() - start
        PRECHECK_LATENCY.observe(elapsed)

        logger.error("guardian_precheck_error", error=str(exc), elapsed_ms=elapsed * 1000)
        REFUSALS_TOTAL.labels(reason_code="SAFETY_UNAVAILABLE").inc()
        return True, "SAFETY_UNAVAILABLE"


def evaluate_detailed(text: str) -> dict:
    """
    Detailed evaluation with full match information.

    Returns dict with:
    - blocked: bool
    - reason_code: str or None
    - matches: list of RuleMatch objects
    - latency_ms: float
    - entropy: float
    """
    start = time.perf_monotonic()

    if not text or not text.strip():
        return {
            "blocked": False,
            "reason_code": None,
            "matches": [],
            "latency_ms": 0.0,
            "entropy": 0.0,
        }

    normalized = text.strip()

    # Check length
    if len(normalized) > _MAX_INPUT_LENGTH:
        return {
            "blocked": True,
            "reason_code": "INPUT_TOO_LONG",
            "matches": [],
            "latency_ms": (time.monotonic() - start) * 1000,
            "entropy": 0.0,
        }

    # GUARDIAN evaluation
    engine = _ensure_guardian()
    matches, eval_latency = engine.evaluate(normalized, use_cache=True)

    # Check for blocking
    blocked = False
    reason_code = None

    for match in matches:
        if match.action in (RuleAction.BLOCK, RuleAction.CANARY):
            blocked = True
            reason_code = match.rule_id.upper()
            break
        elif match.action == RuleAction.ESCALATE and match.severity in (Severity.HIGH, Severity.CRITICAL):
            blocked = True
            reason_code = f"ESCALATE_{match.category.upper()}"
            break

    # Calculate entropy
    entropy = _shannon_entropy(normalized) if len(normalized) > 50 else 0.0

    elapsed = time.monotonic() - start

    return {
        "blocked": blocked,
        "reason_code": reason_code,
        "matches": [m.to_dict() for m in matches],
        "latency_ms": elapsed * 1000,
        "entropy": entropy,
        "eval_latency_ms": eval_latency,
    }


def get_guardian_stats() -> dict:
    """Get GUARDIAN engine statistics."""
    engine = _ensure_guardian()
    return engine.get_stats()


# ---------------------------------------------------------------------------
# Backwards compatibility
# ---------------------------------------------------------------------------
def refresh_blocklist() -> None:
    """
    Legacy function - now handled by GUARDIAN's auto-reload.
    Kept for backwards compatibility.
    """
    logger.debug("refresh_blocklist called (legacy - GUARDIAN handles this)")


# ---------------------------------------------------------------------------
# Initialization on import
# ---------------------------------------------------------------------------
# Initialize GUARDIAN on first use (lazy loading)
# This prevents import-time side effects
