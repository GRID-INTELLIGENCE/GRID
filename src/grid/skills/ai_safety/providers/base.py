"""AI Safety Provider Base Module.

Base classes and utilities for provider-specific safety skills.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from grid.skills.base import SimpleSkill

from ..base import SafetyCategory, SafetyViolation, ThreatLevel

logger = logging.getLogger(__name__)


class ProviderSafetySkill(ABC):
    """Base class for provider-specific safety skills."""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    @abstractmethod
    def check_content(self, content: str, **kwargs: Any) -> list[SafetyViolation]:
        """Check content for safety violations.

        Args:
            content: Content to check.
            **kwargs: Additional provider-specific arguments.

        Returns:
            List of safety violations.
        """
        pass

    def create_violation(
        self,
        category: SafetyCategory,
        severity: ThreatLevel,
        confidence: float,
        description: str,
        evidence: dict[str, Any] | None = None,
    ) -> SafetyViolation:
        """Create a safety violation with provider info.

        Args:
            category: Violation category.
            severity: Threat level.
            confidence: Confidence score.
            description: Description of violation.
            evidence: Optional evidence dictionary.

        Returns:
            SafetyViolation instance.
        """
        return SafetyViolation(
            category=category,
            severity=severity,
            confidence=confidence,
            description=description,
            evidence=evidence or {},
            provider=self.provider_name,
        )


def provider_handler_factory(
    provider_name: str,
    check_func: callable,
    version: str = "1.0.0",
) -> SimpleSkill:
    """Factory function to create provider safety skills.

    Args:
        provider_name: Name of the provider.
        check_func: Function that checks content and returns violations.
        version: Skill version.

    Returns:
        SimpleSkill instance.
    """
    def handler(args: dict[str, Any]) -> dict[str, Any]:
        content = args.get("content", "")
        if not content:
            return {
                "success": True,
                "violations": [],
                "message": "No content provided",
            }

        try:
            violations = check_func(content, **args)
            return {
                "success": True,
                "violations": [v.to_dict() for v in violations],
                "violation_count": len(violations),
                "provider": provider_name,
            }
        except Exception as e:
            logger.error(f"Error in {provider_name} safety check: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": provider_name,
            }

    return SimpleSkill(
        id=f"provider_{provider_name}",
        name=f"{provider_name.title()} Safety Provider",
        description=f"Safety checks using {provider_name.title()} API",
        handler=handler,
        version=version,
    )
