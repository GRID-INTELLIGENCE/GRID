"""OpenAI Safety Provider Skill.

Integrates OpenAI moderation API for content safety checks.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from grid.skills.base import SimpleSkill

from ..base import SafetyCategory, SafetyViolation, ThreatLevel
from ..config import get_config

logger = logging.getLogger(__name__)


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


def check_openai_safety(content: str, **kwargs: Any) -> list[SafetyViolation]:
    """Check content using OpenAI moderation API.

    Args:
        content: Content to check.
        **kwargs: Additional arguments (model, etc.).

    Returns:
        List of safety violations.
    """
    violations = []
    config = get_config()

    # Check if OpenAI is enabled
    if not config.is_provider_enabled("openai"):
        logger.debug("OpenAI provider not enabled")
        return violations

    api_key = config.get_provider_api_key("openai")
    if not api_key:
        logger.warning("OpenAI API key not available")
        return violations

    try:
        # Import here to avoid dependency issues
        import requests

        model = kwargs.get("model", "omni-moderation-latest")

        response = requests.post(
            "https://api.openai.com/v1/moderations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"input": content, "model": model},
            timeout=config.providers["openai"].timeout_seconds,
        )

        if response.status_code != 200:
            logger.warning(f"OpenAI moderation API error: {response.status_code}")
            return violations

        data = response.json()
        results = data.get("results", [])

        if not results:
            return violations

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
                        },
                        provider="openai",
                    )
                    violations.append(violation)

        logger.debug(f"OpenAI check completed: {len(violations)} violations found")

    except ImportError:
        logger.debug("requests not available, skipping OpenAI check")
    except Exception as e:
        logger.error(f"OpenAI safety check error: {e}")

    return violations


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
        }

    violations = check_openai_safety(content, **args)

    return {
        "success": True,
        "violations": [v.to_dict() for v in violations],
        "violation_count": len(violations),
        "provider": "openai",
    }


# Skill instance
provider_openai = SimpleSkill(
    id="provider_openai",
    name="OpenAI Safety Provider",
    description="Safety checks using OpenAI Moderation API",
    handler=openai_handler,
    version="1.0.0",
)
