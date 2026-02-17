"""Governance and policy engine for the legal agent.

Maintains a registry of governance policies, evaluates actions against them,
and prescribes enforcement actions.  Integrates with the boundary engine for
hard-enforcement and with the safety module for wellbeing checks.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from .models import (
    ComplianceAssessment,
    ComplianceStatus,
    GovernanceAction,
    GovernancePolicy,
    PolicyDomain,
    PolicySeverity,
    PolicyViolation,
)

logger = logging.getLogger(__name__)


class GovernanceEngine:
    """Registry-based governance engine that evaluates actions against policies."""

    def __init__(self) -> None:
        self._policies: dict[str, GovernancePolicy] = {}
        self._load_default_policies()

    # -- Policy management ---------------------------------------------------

    def register_policy(self, policy: GovernancePolicy) -> None:
        """Register or update a governance policy."""
        self._policies[policy.policy_id] = policy
        logger.info("policy_registered", extra={"policy_id": policy.policy_id, "name": policy.name})

    def deactivate_policy(self, policy_id: str) -> bool:
        """Soft-delete a policy by marking it inactive."""
        policy = self._policies.get(policy_id)
        if policy is None:
            return False
        policy.active = False
        logger.info("policy_deactivated", extra={"policy_id": policy_id})
        return True

    def get_active_policies(self, domain: PolicyDomain | None = None) -> list[GovernancePolicy]:
        """Return active policies, optionally filtered by domain."""
        now = datetime.now(UTC)
        policies: list[GovernancePolicy] = []
        for p in self._policies.values():
            if not p.active:
                continue
            if p.expires_at and p.expires_at < now:
                continue
            if domain and p.domain != domain:
                continue
            policies.append(p)
        return policies

    # -- Evaluation ----------------------------------------------------------

    async def evaluate(
        self,
        target: str,
        context: dict[str, Any],
        domains: list[PolicyDomain] | None = None,
    ) -> ComplianceAssessment:
        """Evaluate *target* against active policies for the given domains.

        Args:
            target: Identifier for the thing being assessed (e.g. a pipeline name).
            context: Arbitrary key-value context used for condition matching.
            domains: Optional filter to restrict which policy domains to check.

        Returns:
            A ``ComplianceAssessment`` summarising findings.
        """
        policies = self._gather_policies(domains)
        violations: list[PolicyViolation] = []

        for policy in policies:
            violation = self._check_policy(policy, context)
            if violation is not None:
                violations.append(violation)

        score = 1.0 - (len(violations) / max(len(policies), 1))
        status = self._derive_status(violations)

        assessment = ComplianceAssessment(
            target=target,
            status=status,
            policies_checked=[p.policy_id for p in policies],
            violations=violations,
            score=max(score, 0.0),
        )

        logger.info(
            "governance_evaluation_complete",
            extra={
                "target": target,
                "policies_checked": len(policies),
                "violations": len(violations),
                "score": assessment.score,
                "status": status.value,
            },
        )
        return assessment

    # -- Internal helpers ----------------------------------------------------

    def _gather_policies(self, domains: list[PolicyDomain] | None) -> list[GovernancePolicy]:
        if domains:
            policies: list[GovernancePolicy] = []
            for d in domains:
                policies.extend(self.get_active_policies(domain=d))
            return policies
        return self.get_active_policies()

    def _check_policy(
        self,
        policy: GovernancePolicy,
        context: dict[str, Any],
    ) -> PolicyViolation | None:
        """Simple condition-based check.  Each condition string is looked up
        as a key in *context*; a falsy value means the condition is not met."""
        for condition in policy.conditions:
            value = context.get(condition)
            if not value:
                return PolicyViolation(
                    policy_id=policy.policy_id,
                    policy_name=policy.name,
                    severity=policy.severity,
                    description=f"Condition '{condition}' not satisfied for policy '{policy.name}'",
                    evidence=[f"{condition}={value!r}"],
                    recommended_action=policy.prescribed_action,
                )
        return None

    @staticmethod
    def _derive_status(violations: list[PolicyViolation]) -> ComplianceStatus:
        if not violations:
            return ComplianceStatus.COMPLIANT
        severities = {v.severity for v in violations}
        if PolicySeverity.CRITICAL in severities or PolicySeverity.HIGH in severities:
            return ComplianceStatus.NON_COMPLIANT
        return ComplianceStatus.PARTIALLY_COMPLIANT

    # -- Defaults ------------------------------------------------------------

    def _load_default_policies(self) -> None:
        """Seed the engine with baseline governance policies."""
        defaults = [
            GovernancePolicy(
                name="Data Privacy Consent",
                description="All personal data processing must have valid user consent",
                domain=PolicyDomain.DATA_PRIVACY,
                severity=PolicySeverity.CRITICAL,
                conditions=["has_user_consent"],
                prescribed_action=GovernanceAction.DENY,
            ),
            GovernancePolicy(
                name="Data Retention Limit",
                description="Personal data must not be retained beyond the agreed retention period",
                domain=PolicyDomain.DATA_PRIVACY,
                severity=PolicySeverity.HIGH,
                conditions=["within_retention_period"],
                prescribed_action=GovernanceAction.REMEDIATE,
            ),
            GovernancePolicy(
                name="Financial Disclosure",
                description="Financial transactions must be disclosed to the accounting department",
                domain=PolicyDomain.FINANCIAL,
                severity=PolicySeverity.HIGH,
                conditions=["accounting_notified"],
                prescribed_action=GovernanceAction.REQUIRE_REVIEW,
            ),
            GovernancePolicy(
                name="Employment Fair Practice",
                description="Employment decisions must follow non-discrimination rules",
                domain=PolicyDomain.EMPLOYMENT,
                severity=PolicySeverity.CRITICAL,
                conditions=["non_discrimination_verified"],
                prescribed_action=GovernanceAction.DENY,
            ),
            GovernancePolicy(
                name="Consumer Rights Transparency",
                description="Users must be informed about how their data and services are used",
                domain=PolicyDomain.CONSUMER_PROTECTION,
                severity=PolicySeverity.HIGH,
                conditions=["transparency_notice_provided"],
                prescribed_action=GovernanceAction.REQUIRE_CONSENT,
            ),
            GovernancePolicy(
                name="Health and Safety Compliance",
                description="Workplace health and safety standards must be maintained",
                domain=PolicyDomain.HEALTH_SAFETY,
                severity=PolicySeverity.CRITICAL,
                conditions=["safety_standards_met"],
                prescribed_action=GovernanceAction.ESCALATE,
            ),
        ]
        for policy in defaults:
            self.register_policy(policy)
