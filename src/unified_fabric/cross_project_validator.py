"""
Unified Fabric - Cross-Project Policy Validator
==============================================
Simple policy enforcement for cross-project safety events.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PolicyValidationResult:
    """Result of cross-project policy validation."""

    allowed: bool
    reason: str = ""
    severity: str = "low"


class CrossProjectPolicyValidator:
    """Validate cross-project safety events for basic policy compliance."""

    def __init__(
        self,
        allowed_projects: Iterable[str] | None = None,
        allowed_domains: Iterable[str] | None = None,
    ) -> None:
        self.allowed_projects = {p.lower() for p in (allowed_projects or {"grid", "coinbase", "wellness_studio"})}
        self.allowed_domains = {d.lower() for d in (allowed_domains or {"safety", "grid", "coinbase", "revenue"})}

    def validate_context(self, context: dict) -> PolicyValidationResult:
        """Validate basic context requirements."""
        project = str(context.get("project", "")).lower()
        domain = str(context.get("domain", "")).lower()

        if project and project not in self.allowed_projects:
            return PolicyValidationResult(
                allowed=False,
                reason=f"Project '{project}' not permitted",
                severity="high",
            )

        if domain and domain not in self.allowed_domains:
            return PolicyValidationResult(
                allowed=False,
                reason=f"Domain '{domain}' not permitted",
                severity="medium",
            )

        return PolicyValidationResult(allowed=True)

    def validate_payload(self, payload: dict) -> PolicyValidationResult:
        """Validate payload context if present."""
        context = payload.get("context") if isinstance(payload, dict) else None
        if isinstance(context, dict):
            return self.validate_context(context)
        return PolicyValidationResult(allowed=True)


_policy_validator: CrossProjectPolicyValidator | None = None


def get_policy_validator() -> CrossProjectPolicyValidator:
    """Get singleton policy validator."""
    global _policy_validator
    if _policy_validator is None:
        _policy_validator = CrossProjectPolicyValidator()
    return _policy_validator


__all__ = [
    "PolicyValidationResult",
    "CrossProjectPolicyValidator",
    "get_policy_validator",
]
