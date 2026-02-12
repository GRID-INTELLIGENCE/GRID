"""
Escalation handler for the safety enforcement pipeline.

Responsibilities:
- Create audit DB entries for flagged requests.
- Notify human reviewers via Slack / PagerDuty.
- Auto-suspend tokens if severity >= threshold.
- Provide approve/block API for human reviewers.
- Handle systematic misuse (tighten limits, disable features).
"""

from __future__ import annotations

import os
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as aioredis

from safety.audit.db import get_session
from safety.audit.models import AuditRecord, AuditStatus, Severity, TrustTier
from safety.escalation.notifier import notify_pagerduty, notify_slack
from safety.observability.logging_setup import get_logger
from safety.observability.metrics import (
    ESCALATIONS_TOTAL,
    ESCALATION_RESOLUTION_LATENCY,
    FALSE_POSITIVES_TOTAL,
)

logger = get_logger("escalation.handler")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_AUTO_SUSPEND_SEVERITY = os.getenv("SAFETY_AUTO_SUSPEND_SEVERITY", "high")
_MISUSE_WINDOW_SECONDS = int(os.getenv("SAFETY_MISUSE_WINDOW", "3600"))
_MISUSE_THRESHOLD = int(os.getenv("SAFETY_MISUSE_THRESHOLD", "5"))

# Severity ordering for comparison
_SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}

# Redis-backed misuse tracker key prefix (sorted set per user).
# Falls back to in-memory tracking if Redis is unavailable.
_MISUSE_KEY_PREFIX = "grid:misuse:"
_misuse_tracker_fallback: dict[str, list[float]] = defaultdict(list)

# Redis client for stream operations
_redis: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis = aioredis.from_url(url, decode_responses=True)
    return _redis


def _severity_gte(a: str, b: str) -> bool:
    """Return True if severity `a` >= severity `b`."""
    return _SEVERITY_ORDER.get(a, 0) >= _SEVERITY_ORDER.get(b, 0)


# ---------------------------------------------------------------------------
# Core escalation
# ---------------------------------------------------------------------------
async def escalate(
    *,
    request_id: str,
    user_id: str,
    trust_tier: str,
    reason_code: str,
    severity: str,
    input_text: str,
    model_output: str | None = None,
    detector_scores: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> str:
    """
    Handle an escalation event.

    1. Write audit DB record.
    2. Notify reviewers.
    3. Auto-suspend if severity >= threshold.
    4. Check for systematic misuse.
    5. Write to audit-stream for observability.

    Returns the audit record ID.
    """
    audit_id = str(uuid.uuid4())
    tid = trace_id or str(uuid.uuid4())
    scores = detector_scores or {}

    # Map string severity to enum
    sev = (
        Severity(severity)
        if severity in Severity.__members__.values()
        else Severity.MEDIUM
    )
    tier = (
        TrustTier(trust_tier)
        if trust_tier in TrustTier.__members__.values()
        else TrustTier.USER
    )

    # 1. Write audit DB record
    try:
        async with get_session() as session:
            record = AuditRecord(
                id=uuid.UUID(audit_id),
                request_id=request_id,
                user_id=user_id,
                trust_tier=tier,
                input=input_text,
                model_output=model_output,
                detector_scores=scores,
                reason_code=reason_code,
                severity=sev,
                status=AuditStatus.ESCALATED,
                trace_id=tid,
            )
            session.add(record)
        logger.info("audit_record_created", audit_id=audit_id, reason_code=reason_code)
    except Exception as exc:
        logger.error("audit_record_failed", error=str(exc), audit_id=audit_id)
        # Continue with notification even if DB write fails

    # 2. Increment metrics
    ESCALATIONS_TOTAL.labels(severity=severity).inc()

    # 3. Notify reviewers
    await notify_slack(
        audit_id=audit_id,
        request_id=request_id,
        user_id=user_id,
        trust_tier=trust_tier,
        reason_code=reason_code,
        severity=severity,
        input_text=input_text,
        detector_scores=scores,
    )

    if severity in ("critical", "high"):
        await notify_pagerduty(
            audit_id=audit_id,
            reason_code=reason_code,
            severity=severity,
            summary=input_text[:200],
        )

    # 4. Auto-suspend if severity >= threshold
    if _severity_gte(severity, _AUTO_SUSPEND_SEVERITY):
        await _suspend_user(user_id, audit_id, reason_code)

    # 5. Check for systematic misuse
    await _check_misuse(user_id)

    # 6. Write to Redis audit-stream
    try:
        client = await _get_redis()
        await client.xadd(
            "audit-stream",
            {
                "event": "escalation",
                "request_id": request_id,
                "user_id": user_id,
                "reason": reason_code,
                "severity": severity,
                "audit_id": audit_id,
            },
        )
    except Exception as exc:
        logger.error("audit_stream_write_failed", error=str(exc))

    return audit_id


# ---------------------------------------------------------------------------
# Human review API
# ---------------------------------------------------------------------------
async def approve(
    request_id: str,
    decision: str,
    reviewer_id: str,
    notes: str = "",
) -> bool:
    """
    Human reviewer approves or blocks an escalated request.

    decision: "approve" or "block"
    """
    try:
        async with get_session() as session:
            from sqlalchemy import select

            stmt = select(AuditRecord).where(
                AuditRecord.request_id == request_id,
                AuditRecord.status == AuditStatus.ESCALATED,
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()

            if record is None:
                logger.warning("approve_record_not_found", request_id=request_id)
                return False

            record.status = AuditStatus.RESOLVED
            record.resolved_at = datetime.now(UTC)
            record.reviewer_id = reviewer_id
            record.notes = f"[{decision}] {notes}"

            # 5c. Resolution latency
            resolution_time = (datetime.now(UTC) - record.created_at).total_seconds()
            ESCALATION_RESOLUTION_LATENCY.observe(resolution_time)

        if decision == "approve":
            # Release the stored model output to response-stream
            if record.model_output:
                try:
                    client = await _get_redis()
                    await client.xadd(
                        "response-stream",
                        {
                            "request_id": request_id,
                            "response": record.model_output,
                            "status": "approved",
                        },
                    )
                except Exception as exc:
                    logger.error("response_release_failed", error=str(exc))

            # Track false positive
            FALSE_POSITIVES_TOTAL.labels(reason_code=record.reason_code).inc()

            logger.info(
                "escalation_approved",
                request_id=request_id,
                reviewer_id=reviewer_id,
            )
        elif decision == "block":
            # Add to dynamic blocklist for pre-check
            try:
                client = await _get_redis()
                # Add a normalized version of the input to the blocklist
                await client.sadd("dynamic_blocklist", record.input.lower().strip())
            except Exception as exc:
                logger.error("blocklist_update_failed", error=str(exc))

            logger.info(
                "escalation_blocked",
                request_id=request_id,
                reviewer_id=reviewer_id,
            )

        return True

    except Exception as exc:
        logger.error("approve_failed", request_id=request_id, error=str(exc))
        return False


# ---------------------------------------------------------------------------
# Systematic misuse detection
# ---------------------------------------------------------------------------
async def _check_misuse(user_id: str) -> None:
    """
    Check if the user has exceeded the misuse threshold within the window.

    Uses Redis sorted sets for cross-instance tracking. Falls back to
    in-memory tracking if Redis is unavailable.
    """
    import time

    now = time.time()
    cutoff = now - _MISUSE_WINDOW_SECONDS

    # Try Redis-backed sliding window first
    try:
        client = await _get_redis()
        key = f"{_MISUSE_KEY_PREFIX}{user_id}"
        pipe = client.pipeline()
        pipe.zremrangebyscore(key, "-inf", cutoff)  # Prune old entries
        pipe.zadd(key, {str(now): now})  # Add current event
        pipe.zcard(key)  # Count events in window
        pipe.expire(key, _MISUSE_WINDOW_SECONDS + 60)  # TTL with buffer
        results = await pipe.execute()
        count = results[2]
    except Exception as exc:
        # Fall back to in-memory tracking if Redis fails
        logger.warning("misuse_tracker_redis_fallback", error=str(exc))
        window = _misuse_tracker_fallback[user_id]
        window = [t for t in window if now - t < _MISUSE_WINDOW_SECONDS]
        window.append(now)
        _misuse_tracker_fallback[user_id] = window
        count = len(window)

    if count >= _MISUSE_THRESHOLD:
        logger.warning(
            "systematic_misuse_detected",
            user_id=user_id,
            escalation_count=len(window),
            window_seconds=_MISUSE_WINDOW_SECONDS,
        )

        # Tighten rate limits
        from safety.api.rate_limiter import tighten_limits

        await tighten_limits(user_id, factor=0.25)

        # Suspend user
        await _suspend_user(user_id, "misuse-auto", "SYSTEMATIC_MISUSE")

        # Write audit-stream event
        try:
            client = await _get_redis()
            await client.xadd(
                "audit-stream",
                {
                    "event": "systematic_misuse",
                    "user_id": user_id,
                    "escalation_count": str(len(window)),
                },
            )
        except Exception:
            pass


async def _suspend_user(user_id: str, audit_id: str, reason: str) -> None:
    """Suspend a user's token in Redis."""
    try:
        client = await _get_redis()
        await client.set(
            f"suspended:{user_id}",
            f"{reason}:{audit_id}",
            ex=86400,  # 24-hour suspension by default
        )
        logger.warning(
            "user_suspended",
            user_id=user_id,
            audit_id=audit_id,
            reason=reason,
        )
    except Exception as exc:
        logger.error("user_suspension_failed", user_id=user_id, error=str(exc))


async def is_user_suspended(user_id: str) -> tuple[bool, str | None]:
    """Check if a user is suspended. Returns (suspended, reason).

    FAIL-CLOSED: If Redis is unavailable, assume user IS suspended.
    This is consistent with the rest of the safety pipeline's fail-closed design.
    Fixed per security audit 2026-02-07 — previous implementation failed OPEN.
    """
    try:
        client = await _get_redis()
        val = await client.get(f"suspended:{user_id}")
        if val:
            return True, val
        return False, None
    except Exception as exc:
        logger.error("suspension_check_failed", user_id=user_id, error=str(exc))
        # FAIL CLOSED: if we can't verify suspension status, deny access
        return True, "SUSPENSION_CHECK_UNAVAILABLE"
