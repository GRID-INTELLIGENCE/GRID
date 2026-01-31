"""Mistral Safety Provider Skill.

Implements Mistral multilingual safety checks.
"""

from __future__ import annotations

import logging
from typing import Any

from grid.skills.base import SimpleSkill

from ..base import SafetyCategory, SafetyViolation, ThreatLevel
from ..config import get_config

logger = logging.getLogger(__name__)


def check_mistral_safety(content: str, **kwargs: Any) -> list[SafetyViolation]:
    """Check content using Mistral's multilingual safety approach.

    Implements language-agnostic safety checks following Mistral's
    focus on multilingual capabilities.

    Args:
        content: Content to check.
        **kwargs: Additional arguments (languages).

    Returns:
        List of safety violations.
    """
    violations = []
    config = get_config()

    if not config.is_provider_enabled("mistral"):
        logger.debug("Mistral provider not enabled")
        return violations

    languages = kwargs.get("languages", ["en"])

    # Multilingual harmful content patterns
    # These are language-agnostic or common across languages
    harmful_patterns = {
        "universal_symbols": [
            "卍", "✠", "☠",  # Symbol-based hate
        ],
        "code_words": [
            "1488", "88", "14 words",  # Known hate codes
            "kkk", "nazi", "fascist",
        ],
    }

    normalized_content = content.lower()

    # Check universal symbols
    for symbol in harmful_patterns["universal_symbols"]:
        if symbol in content:
            violation = SafetyViolation(
                category=SafetyCategory.HARMFUL_CONTENT,
                severity=ThreatLevel.CRITICAL,
                confidence=0.9,
                description="Harmful symbol detected",
                evidence={
                    "symbol": symbol,
                    "detection_type": "universal_symbol",
                    "languages_checked": languages,
                },
                provider="mistral",
            )
            violations.append(violation)

    # Check code words
    for code in harmful_patterns["code_words"]:
        if code in normalized_content:
            violation = SafetyViolation(
                category=SafetyCategory.HARMFUL_CONTENT,
                severity=ThreatLevel.HIGH,
                confidence=0.85,
                description="Potentially coded hate speech",
                evidence={
                    "code": code,
                    "detection_type": "code_word",
                    "languages_checked": languages,
                },
                provider="mistral",
            )
            violations.append(violation)

    logger.debug(f"Mistral check completed: {len(violations)} violations found")
    return violations


def mistral_handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle Mistral safety checks.

    Args:
        args: Dictionary containing:
            - content: str, required
            - languages: list, optional (default: ["en"])

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
    kwargs = {k: v for k, v in args.items() if k != "content"}
    violations = check_mistral_safety(content, **kwargs)

    return {
        "success": True,
        "violations": [v.to_dict() for v in violations],
        "violation_count": len(violations),
        "provider": "mistral",
    }


# Skill instance
provider_mistral = SimpleSkill(
    id="provider_mistral",
    name="Mistral Safety Provider",
    description="Multilingual safety checks using Mistral approach",
    handler=mistral_handler,
    version="1.0.0",
)
