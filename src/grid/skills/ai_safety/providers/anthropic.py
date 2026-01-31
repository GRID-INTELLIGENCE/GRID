"""Anthropic Safety Provider Skill.

Implements Anthropic Constitutional AI checks.
"""

from __future__ import annotations

import logging
from typing import Any

from grid.skills.base import SimpleSkill

from ..base import SafetyCategory, SafetyViolation, ThreatLevel
from ..config import get_config

logger = logging.getLogger(__name__)


CONSTITUTIONAL_PRINCIPLES = [
    "Choose the response that is most helpful, honest, and harmless.",
    "Choose the response that is least likely to be harmful or offensive.",
    "Choose the response that shows the most respect for human rights and dignity.",
]


def check_anthropic_safety(content: str, **kwargs: Any) -> list[SafetyViolation]:
    """Check content using Anthropic's approach.

    Note: This is a local implementation following Anthropic's Constitutional AI
    principles. For actual API integration, Anthropic's API would be used.

    Args:
        content: Content to check.
        **kwargs: Additional arguments.

    Returns:
        List of safety violations.
    """
    violations = []
    config = get_config()

    # Check if Anthropic is enabled
    if not config.is_provider_enabled("anthropic"):
        logger.debug("Anthropic provider not enabled")
        return violations

    # Local pattern-based checks following Constitutional AI principles
    harmful_patterns = {
        "harmful_instructions": [
            "how to make", "how to build", "instructions for",
            "step by step", "tutorial on",
        ],
        "discrimination": [
            "inferior race", "superior race", "racial purity",
            "ethnic cleansing", "discriminate against",
        ],
        "manipulation": [
            "manipulate", "deceive", "trick into", "scam",
            "fraud", "exploit",
        ],
    }

    normalized_content = content.lower()

    # Check for harmful patterns
    for category, patterns in harmful_patterns.items():
        for pattern in patterns:
            if pattern in normalized_content:
                violation = SafetyViolation(
                    category=SafetyCategory.HARMFUL_CONTENT,
                    severity=ThreatLevel.HIGH,
                    confidence=0.75,
                    description=f"Potentially harmful content: {category}",
                    evidence={
                        "pattern": pattern,
                        "category": category,
                        "principle": "Choose the response that is least likely to be harmful",
                    },
                    provider="anthropic",
                )
                violations.append(violation)
                break  # One violation per category is sufficient

    logger.debug(f"Anthropic check completed: {len(violations)} violations found")
    return violations


def anthropic_handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle Anthropic safety checks.

    Args:
        args: Dictionary containing:
            - content: str, required
            - constitution_version: str, optional

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

    violations = check_anthropic_safety(content, **args)

    return {
        "success": True,
        "violations": [v.to_dict() for v in violations],
        "violation_count": len(violations),
        "provider": "anthropic",
        "principles_checked": len(CONSTITUTIONAL_PRINCIPLES),
    }


# Skill instance
provider_anthropic = SimpleSkill(
    id="provider_anthropic",
    name="Anthropic Safety Provider",
    description="Safety checks using Anthropic Constitutional AI principles",
    handler=anthropic_handler,
    version="1.0.0",
)
