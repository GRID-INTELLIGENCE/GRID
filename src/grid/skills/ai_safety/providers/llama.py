"""Llama Safety Provider Skill.

Implements Llama Guard patterns for input/output safety.
"""

from __future__ import annotations

import logging
from typing import Any

from grid.skills.base import SimpleSkill

from ..base import SafetyCategory, SafetyViolation, ThreatLevel
from ..config import get_config

logger = logging.getLogger(__name__)


def check_llama_safety(content: str, **kwargs: Any) -> list[SafetyViolation]:
    """Check content using Llama Guard approach.

    Implements input/output guard patterns similar to Llama Guard
    for comprehensive content safety.

    Args:
        content: Content to check.
        **kwargs: Additional arguments (guard_type).

    Returns:
        List of safety violations.
    """
    violations = []
    config = get_config()

    if not config.is_provider_enabled("llama"):
        logger.debug("Llama provider not enabled")
        return violations

    guard_type = kwargs.get("guard_type", "input")  # input or output

    # Llama Guard-style categories
    if guard_type == "input":
        # Input guard - check user prompts
        unsafe_patterns = {
            "harmful_instructions": [
                "how do i", "how to", "instructions for",
                "steps to", "guide for making",
            ],
            "jailbreak_attempts": [
                "ignore previous", "disregard instructions",
                "new mode", "developer mode", "DAN",
                "do anything now", "jailbreak",
            ],
            "role_play_exploits": [
                "pretend to be", "act as", "roleplay as",
                "you are now", "simulate being",
            ],
        }
    else:
        # Output guard - check model responses
        unsafe_patterns = {
            "harmful_content": [
                "here is how", "step 1:", "ingredients:",
                "materials needed", "procedure:",
            ],
            "biased_output": [
                "all people", "everyone knows", "obviously",
                "clearly superior", "inferior race",
            ],
        }

    normalized_content = content.lower()

    for category, patterns in unsafe_patterns.items():
        for pattern in patterns:
            if pattern in normalized_content:
                # Determine severity based on category
                if category in ["jailbreak_attempts", "harmful_instructions"]:
                    severity = ThreatLevel.HIGH
                    confidence = 0.85
                elif category == "role_play_exploits":
                    severity = ThreatLevel.MEDIUM
                    confidence = 0.75
                else:
                    severity = ThreatLevel.MEDIUM
                    confidence = 0.7

                violation = SafetyViolation(
                    category=SafetyCategory.HARMFUL_CONTENT,
                    severity=severity,
                    confidence=confidence,
                    description=f"Llama Guard: {category.replace('_', ' ')} ({guard_type})",
                    evidence={
                        "pattern": pattern,
                        "category": category,
                        "guard_type": guard_type,
                        "llama_category": f"S{list(unsafe_patterns.keys()).index(category) + 1}",
                    },
                    provider="llama",
                )
                violations.append(violation)
                break  # One per category

    logger.debug(f"Llama check completed: {len(violations)} violations found")
    return violations


def llama_handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle Llama safety checks.

    Args:
        args: Dictionary containing:
            - content: str, required
            - guard_type: str, optional (input/output, default: input)

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
    violations = check_llama_safety(content, **kwargs)

    return {
        "success": True,
        "violations": [v.to_dict() for v in violations],
        "violation_count": len(violations),
        "provider": "llama",
        "guard_type": args.get("guard_type", "input"),
    }


# Skill instance
provider_llama = SimpleSkill(
    id="provider_llama",
    name="Llama Safety Provider",
    description="Safety checks using Llama Guard patterns",
    handler=llama_handler,
    version="1.0.0",
)
