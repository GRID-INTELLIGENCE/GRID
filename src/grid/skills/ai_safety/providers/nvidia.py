"""NVIDIA Safety Provider Skill.

Integrates NVIDIA Guardrails for content safety.
"""

from __future__ import annotations

import logging
from typing import Any

from grid.skills.base import SimpleSkill

from ..base import SafetyCategory, SafetyViolation, ThreatLevel
from ..config import get_config

logger = logging.getLogger(__name__)


def check_nvidia_safety(content: str, **kwargs: Any) -> list[SafetyViolation]:
    """Check content using NVIDIA Guardrails approach.

    Implements guardrail-style safety checks for enterprise
    deployment scenarios.

    Args:
        content: Content to check.
        **kwargs: Additional arguments (guardrail_config).

    Returns:
        List of safety violations.
    """
    violations = []
    config = get_config()

    if not config.is_provider_enabled("nvidia"):
        logger.debug("NVIDIA provider not enabled")
        return violations

    guardrail_config = kwargs.get("guardrail_config", {})

    # NVIDIA-style guardrail checks
    # Enterprise-focused safety categories
    enterprise_risks = {
        "data_exfiltration": [
            "confidential", "proprietary", "trade secret",
            "internal only", "not for distribution",
        ],
        "compliance_violation": [
            "hipaa", "gdpr violation", "pci-dss", "sox",
            "regulatory violation", "non-compliant",
        ],
        "security_risk": [
            "exploit", "vulnerability", "zero-day", "cve-",
            "security flaw", "breach method",
        ],
    }

    normalized_content = content.lower()

    for risk_type, patterns in enterprise_risks.items():
        for pattern in patterns:
            if pattern in normalized_content:
                # Map to appropriate category
                category_map = {
                    "data_exfiltration": SafetyCategory.PRIVACY_VIOLATION,
                    "compliance_violation": SafetyCategory.MISINFORMATION,
                    "security_risk": SafetyCategory.HARMFUL_CONTENT,
                }

                safety_cat = category_map.get(risk_type, SafetyCategory.HARMFUL_CONTENT)
                severity = ThreatLevel.HIGH if risk_type == "security_risk" else ThreatLevel.MEDIUM

                violation = SafetyViolation(
                    category=safety_cat,
                    severity=severity,
                    confidence=0.8,
                    description=f"NVIDIA guardrail: {risk_type.replace('_', ' ')}",
                    evidence={
                        "pattern": pattern,
                        "risk_type": risk_type,
                        "guardrail": "enterprise_security",
                    },
                    provider="nvidia",
                )
                violations.append(violation)
                break

    logger.debug(f"NVIDIA check completed: {len(violations)} violations found")
    return violations


def nvidia_handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle NVIDIA safety checks.

    Args:
        args: Dictionary containing:
            - content: str, required
            - guardrail_config: dict, optional

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
    violations = check_nvidia_safety(content, **kwargs)

    return {
        "success": True,
        "violations": [v.to_dict() for v in violations],
        "violation_count": len(violations),
        "provider": "nvidia",
    }


# Skill instance
provider_nvidia = SimpleSkill(
    id="provider_nvidia",
    name="NVIDIA Safety Provider",
    description="Safety checks using NVIDIA Guardrails approach",
    handler=nvidia_handler,
    version="1.0.0",
)
