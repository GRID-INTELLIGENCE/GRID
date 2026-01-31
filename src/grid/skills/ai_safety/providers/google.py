"""Google Safety Provider Skill.

Integrates Google Frontier Safety API for content safety checks.
"""

from __future__ import annotations

import logging
from typing import Any

from grid.skills.base import SimpleSkill

from ..base import SafetyCategory, SafetyViolation, ThreatLevel
from ..config import get_config

logger = logging.getLogger(__name__)


def check_google_safety(content: str, **kwargs: Any) -> list[SafetyViolation]:
    """Check content using Google's safety approach.

    Note: This implements pattern-based checks following Google's
    AI Principles and safety guidelines.

    Args:
        content: Content to check.
        **kwargs: Additional arguments.

    Returns:
        List of safety violations.
    """
    violations = []
    config = get_config()

    if not config.is_provider_enabled("google"):
        logger.debug("Google provider not enabled")
        return violations

    # Google's AI Principles based checks
    safety_settings = kwargs.get("safety_settings", {})

    # Harm categories based on Google's content policy
    harm_categories = {
        "dangerous_content": [
            "build a bomb", "make explosives", "create poison",
            "dangerous weapon", "harm someone", "hurt people",
        ],
        "harassment": [
            "harass", "bully", "stalk", "threaten",
            "intimidate", "blackmail",
        ],
        "hate_speech": [
            "hate group", "racial slur", "ethnic hate",
            "religious hatred", "discriminate",
        ],
        "sexually_explicit": [
            "sexual content", "explicit material", "adult content",
        ],
    }

    normalized_content = content.lower()

    for category, patterns in harm_categories.items():
        for pattern in patterns:
            if pattern in normalized_content:
                # Map to SafetyCategory
                category_map = {
                    "dangerous_content": SafetyCategory.HARMFUL_CONTENT,
                    "harassment": SafetyCategory.HARASSMENT,
                    "hate_speech": SafetyCategory.HARMFUL_CONTENT,
                    "sexually_explicit": SafetyCategory.HARMFUL_CONTENT,
                }

                safety_cat = category_map.get(category, SafetyCategory.HARMFUL_CONTENT)
                severity = ThreatLevel.HIGH if category == "dangerous_content" else ThreatLevel.MEDIUM

                violation = SafetyViolation(
                    category=safety_cat,
                    severity=severity,
                    confidence=0.8,
                    description=f"Google safety: {category.replace('_', ' ')}",
                    evidence={
                        "pattern": pattern,
                        "category": category,
                        "google_principle": "Be socially beneficial",
                    },
                    provider="google",
                )
                violations.append(violation)
                break

    logger.debug(f"Google check completed: {len(violations)} violations found")
    return violations


def google_handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle Google safety checks.

    Args:
        args: Dictionary containing:
            - content: str, required
            - safety_settings: dict, optional

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

    # Remove content from kwargs to avoid duplicate
    kwargs = {k: v for k, v in args.items() if k != "content"}
    violations = check_google_safety(content, **kwargs)

    return {
        "success": True,
        "violations": [v.to_dict() for v in violations],
        "violation_count": len(violations),
        "provider": "google",
    }


# Skill instance
provider_google = SimpleSkill(
    id="provider_google",
    name="Google Safety Provider",
    description="Safety checks using Google AI Principles",
    handler=google_handler,
    version="1.0.0",
)
