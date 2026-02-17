"""OpenAI Safety Provider Skill.

Integrates OpenAI moderation API for content safety checks.
"""

from __future__ import annotations

import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Any

from grid.skills.base import SimpleSkill

from ..base import SafetyCategory, SafetyViolation, ThreatLevel
from ..config import get_config

logger = logging.getLogger(__name__)

TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}
DEFAULT_MAX_RETRIES = 2
DEFAULT_BACKOFF_BASE_SECONDS = 0.5


@dataclass
class OpenAISafetyCheckResult:
    """Result object for OpenAI safety checks."""

    violations: list[SafetyViolation]
    check_performed: bool
    degraded: bool
    origin: str
    reason: str | None = None
    error: str | None = None
    request_id: str | None = None
    retries_attempted: int = 0


def _parse_bool(value: Any, default: bool = True) -> bool:
    """Parse a bool-like value from request args/env values."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _backoff_delay_seconds(attempt: int, retry_after: str | None = None, base_seconds: float = 0.5) -> float:
    """Compute exponential backoff with jitter and Retry-After support."""
    if retry_after:
        try:
            parsed = float(retry_after)
            if parsed > 0:
                return min(parsed, 30.0)
        except ValueError:
            pass

    raw_delay = base_seconds * (2**attempt)
    jitter = random.uniform(0.0, base_seconds)  # noqa: S311
    return min(raw_delay + jitter, 30.0)


def map_openai_category(category: str) -> SafetyCategory:
    """Map OpenAI moderation category to SafetyCategory.

    Args:
        category: OpenAI category string.

    Returns:
        Mapped SafetyCategory.
    """
    category_map = {
        "hate": SafetyCategory.HARASSMENT,
        "hate/threatening": SafetyCategory.HARMFUL_CONTENT,
        "harassment": SafetyCategory.HARASSMENT,
        "harassment/threatening": SafetyCategory.HARMFUL_CONTENT,
        "self-harm": SafetyCategory.MENTAL_HEALTH_RISK,
        "self-harm/instructions": SafetyCategory.MENTAL_HEALTH_RISK,
        "self-harm/intent": SafetyCategory.MENTAL_HEALTH_RISK,
        "sexual": SafetyCategory.HARMFUL_CONTENT,
        "sexual/minors": SafetyCategory.HARMFUL_CONTENT,
        "violence": SafetyCategory.HARMFUL_CONTENT,
        "violence/graphic": SafetyCategory.HARMFUL_CONTENT,
    }
    return category_map.get(category, SafetyCategory.HARMFUL_CONTENT)


def map_openai_score(score: float) -> ThreatLevel:
    """Map OpenAI score to ThreatLevel.

    Args:
        score: OpenAI moderation score (0.0 to 1.0).

    Returns:
        Mapped ThreatLevel.
    """
    if score >= 0.8:
        return ThreatLevel.CRITICAL
    elif score >= 0.6:
        return ThreatLevel.HIGH
    elif score >= 0.4:
        return ThreatLevel.MEDIUM
    elif score >= 0.2:
        return ThreatLevel.LOW
    else:
        return ThreatLevel.NONE


def check_openai_safety_detailed(content: str, **kwargs: Any) -> OpenAISafetyCheckResult:
    """Run OpenAI moderation with explicit degradation metadata.

    Args:
        content: Content to check.
        **kwargs: Additional arguments (model, etc.).

    Returns:
        Detailed check result including provenance and degradation state.
    """
    violations: list[SafetyViolation] = []
    config = get_config()
    try:
        max_retries = max(
            0,
            int(
                kwargs.get(
                    "max_retries",
                    os.getenv("AI_SAFETY_OPENAI_MAX_RETRIES", str(DEFAULT_MAX_RETRIES)),
                )
            ),
        )
    except (TypeError, ValueError):
        max_retries = DEFAULT_MAX_RETRIES

    try:
        backoff_base_seconds = float(
            kwargs.get(
                "retry_base_seconds",
                os.getenv(
                    "AI_SAFETY_OPENAI_RETRY_BASE_SECONDS",
                    str(DEFAULT_BACKOFF_BASE_SECONDS),
                ),
            )
        )
    except (TypeError, ValueError):
        backoff_base_seconds = DEFAULT_BACKOFF_BASE_SECONDS

    model = kwargs.get("model", "omni-moderation-latest")

    # Check if OpenAI is enabled
    if not config.is_provider_enabled("openai"):
        logger.debug("OpenAI provider not enabled")
        return OpenAISafetyCheckResult(
            violations=[],
            check_performed=False,
            degraded=False,
            origin="skipped",
            reason="provider_not_enabled",
        )

    api_key = config.get_provider_api_key("openai")
    if not api_key:
        logger.warning("OpenAI API key not available")
        return OpenAISafetyCheckResult(
            violations=[],
            check_performed=False,
            degraded=False,
            origin="skipped",
            reason="missing_api_key",
        )

    try:
        # Import here to avoid dependency issues
        import requests  # type: ignore[import-untyped]

    except ImportError:
        logger.error("requests not available for OpenAI safety checks")
        return OpenAISafetyCheckResult(
            violations=[],
            check_performed=True,
            degraded=True,
            origin="degraded",
            reason="missing_http_client",
            error="requests_not_available",
        )

    response: Any | None = None
    retries_attempted = 0

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                "https://api.openai.com/v1/moderations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"input": content, "model": model},
                timeout=config.providers["openai"].timeout_seconds,
            )
        except Exception as exc:
            if attempt < max_retries:
                retries_attempted += 1
                sleep_for = _backoff_delay_seconds(attempt=attempt, base_seconds=backoff_base_seconds)
                logger.warning(
                    "OpenAI moderation transport error (attempt %s/%s): %s; retrying in %.2fs",
                    attempt + 1,
                    max_retries + 1,
                    exc,
                    sleep_for,
                )
                time.sleep(sleep_for)
                continue

            logger.error("OpenAI safety check transport error: %s", exc)
            return OpenAISafetyCheckResult(
                violations=[],
                check_performed=True,
                degraded=True,
                origin="degraded",
                reason="transport_error",
                error=str(exc),
                retries_attempted=retries_attempted,
            )

        if response.status_code == 200:
            break

        request_id = response.headers.get("x-request-id")
        if response.status_code in TRANSIENT_STATUS_CODES and attempt < max_retries:
            retries_attempted += 1
            sleep_for = _backoff_delay_seconds(
                attempt=attempt,
                retry_after=response.headers.get("Retry-After"),
                base_seconds=backoff_base_seconds,
            )
            logger.warning(
                "OpenAI moderation transient error status=%s request_id=%s (attempt %s/%s), retrying in %.2fs",
                response.status_code,
                request_id,
                attempt + 1,
                max_retries + 1,
                sleep_for,
            )
            time.sleep(sleep_for)
            continue

        return OpenAISafetyCheckResult(
            violations=[],
            check_performed=True,
            degraded=True,
            origin="degraded",
            reason=f"http_{response.status_code}",
            error=f"OpenAI moderation API error: {response.status_code}",
            request_id=request_id,
            retries_attempted=retries_attempted,
        )

    if response is None:
        return OpenAISafetyCheckResult(
            violations=[],
            check_performed=True,
            degraded=True,
            origin="degraded",
            reason="no_response",
            error="No response received from OpenAI moderation API",
            retries_attempted=retries_attempted,
        )

    request_id = response.headers.get("x-request-id")

    try:
        data = response.json()
    except Exception as exc:
        return OpenAISafetyCheckResult(
            violations=[],
            check_performed=True,
            degraded=True,
            origin="degraded",
            reason="invalid_json",
            error=str(exc),
            request_id=request_id,
            retries_attempted=retries_attempted,
        )

    results = data.get("results", [])
    if not results:
        return OpenAISafetyCheckResult(
            violations=[],
            check_performed=True,
            degraded=False,
            origin="live",
            reason="no_results",
            request_id=request_id,
            retries_attempted=retries_attempted,
        )

    result = results[0]
    categories = result.get("categories", {})
    category_scores = result.get("category_scores", {})

    for category, flagged in categories.items():
        if flagged:
            score = category_scores.get(category, 0.0)
            safety_category = map_openai_category(category)
            threat_level = map_openai_score(score)

            if threat_level != ThreatLevel.NONE:
                violation = SafetyViolation(
                    category=safety_category,
                    severity=threat_level,
                    confidence=score,
                    description=f"OpenAI flagged: {category}",
                    evidence={
                        "provider_category": category,
                        "score": score,
                        "model": model,
                        "request_id": request_id,
                    },
                    provider="openai",
                )
                violations.append(violation)

    logger.debug("OpenAI check completed: %s violations found", len(violations))
    return OpenAISafetyCheckResult(
        violations=violations,
        check_performed=True,
        degraded=False,
        origin="live",
        request_id=request_id,
        retries_attempted=retries_attempted,
    )


def check_openai_safety(content: str, **kwargs: Any) -> list[SafetyViolation]:
    """Legacy compatibility wrapper returning only violations."""
    result = check_openai_safety_detailed(content, **kwargs)
    if result.degraded:
        logger.warning("OpenAI safety check degraded (%s): %s", result.reason, result.error)
    return result.violations


def openai_handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle OpenAI safety checks.

    Args:
        args: Dictionary containing:
            - content: str, required
            - model: str, optional (default: omni-moderation-latest)

    Returns:
        Dictionary with violations.
    """
    content = args.get("content", "")
    if not content:
        return {
            "success": True,
            "violations": [],
            "message": "No content provided",
            "origin": "skipped",
            "degraded": False,
        }

    # Remove content from kwargs to avoid duplicate
    kwargs = {k: v for k, v in args.items() if k != "content"}
    fail_closed = _parse_bool(
        kwargs.pop("fail_closed", os.getenv("AI_SAFETY_OPENAI_FAIL_CLOSED")),
        default=True,
    )
    result = check_openai_safety_detailed(content, **kwargs)

    if result.degraded:
        if fail_closed:
            return {
                "success": False,
                "violations": [],
                "violation_count": 0,
                "provider": "openai",
                "degraded": True,
                "origin": result.origin,
                "reason": result.reason,
                "error": result.error or "OpenAI moderation unavailable",
                "request_id": result.request_id,
                "retries_attempted": result.retries_attempted,
                "fail_closed": True,
            }

        logger.warning("OpenAI safety check degraded in fail-open mode: %s", result.reason)
        return {
            "success": True,
            "violations": [],
            "violation_count": 0,
            "provider": "openai",
            "degraded": True,
            "origin": result.origin,
            "reason": result.reason,
            "warning": result.error or "OpenAI moderation unavailable; fail-open override enabled",
            "request_id": result.request_id,
            "retries_attempted": result.retries_attempted,
            "fail_closed": False,
        }

    return {
        "success": True,
        "violations": [v.to_dict() for v in result.violations],
        "violation_count": len(result.violations),
        "provider": "openai",
        "degraded": False,
        "origin": result.origin,
        "request_id": result.request_id,
        "retries_attempted": result.retries_attempted,
    }


# Skill instance
provider_openai = SimpleSkill(
    id="provider_openai",
    name="OpenAI Safety Provider",
    description="Safety checks using OpenAI Moderation API",
    handler=openai_handler,
    version="1.0.0",
)
