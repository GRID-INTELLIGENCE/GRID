"""Compliance monitoring module.

Provides continuous and on-demand compliance checks that tie together
the governance engine, user-rights manager, and boundary/safety layers.
"""

from __future__ import annotations

import logging
from typing import Any

from .governance import GovernanceEngine
from .models import (
    ComplianceAssessment,
    ComplianceStatus,
    PolicyDomain,
    PolicySeverity,
    PolicyViolation,
)
from .user_rights import UserRightsManager

logger = logging.getLogger(__name__)


class ComplianceMonitor:
    """Orchestrates compliance checks across governance and user-rights."""

    def __init__(
        self,
        governance_engine: GovernanceEngine,
        user_rights_manager: UserRightsManager,
    ) -> None:
        self._governance = governance_engine
        self._rights = user_rights_manager

    async def run_full_check(
        self,
        target: str,
        context: dict[str, Any],
        user_id: str | None = None,
        domains: list[PolicyDomain] | None = None,
    ) -> ComplianceAssessment:
        """Run governance evaluation plus supplementary checks.

        This is the main entry point for a comprehensive compliance review.
        """
        assessment = await self._governance.evaluate(target, context, domains)

        # Check for overdue user-right requests — each one is a violation.
        if user_id:
            overdue = self._rights.get_overdue_requests()
            user_overdue = [r for r in overdue if r.user_id == user_id]
            for req in user_overdue:
                assessment.violations.append(
                    PolicyViolation(
                        policy_id="builtin_user_right_sla",
                        policy_name="User Right Response SLA",
                        severity=PolicySeverity.HIGH,
                        description=(
                            f"User-right request '{req.request_id}' ({req.right_type.value}) "
                            "has exceeded the response SLA"
                        ),
                        evidence=[f"request_id={req.request_id}", f"submitted_at={req.submitted_at.isoformat()}"],
                    )
                )

        # Re-derive status after additional violations.
        if assessment.violations:
            severities = {v.severity for v in assessment.violations}
            if PolicySeverity.CRITICAL in severities or PolicySeverity.HIGH in severities:
                assessment.status = ComplianceStatus.NON_COMPLIANT
            elif assessment.status == ComplianceStatus.COMPLIANT:
                assessment.status = ComplianceStatus.PARTIALLY_COMPLIANT

            total = len(assessment.policies_checked) + len(assessment.violations)
            assessment.score = max(1.0 - len(assessment.violations) / max(total, 1), 0.0)

        logger.info(
            "compliance_check_complete",
            extra={
                "target": target,
                "status": assessment.status.value,
                "violations": len(assessment.violations),
                "score": assessment.score,
            },
        )
        return assessment

    async def check_safety_boundaries(
        self,
        context: dict[str, Any],
    ) -> list[PolicyViolation]:
        """Check for safety and boundary-related violations.

        Validates that safety standards and boundary constraints are respected
        in the given operational context.
        """
        violations: list[PolicyViolation] = []

        if not context.get("boundary_engine_active", True):
            violations.append(
                PolicyViolation(
                    policy_id="builtin_boundary_active",
                    policy_name="Boundary Engine Active",
                    severity=PolicySeverity.CRITICAL,
                    description="Boundary engine is not active — enforcement cannot be guaranteed",
                    recommended_action=_governance_action_escalate(),
                )
            )

        if not context.get("safety_checks_passed", True):
            violations.append(
                PolicyViolation(
                    policy_id="builtin_safety_checks",
                    policy_name="Safety Checks Passed",
                    severity=PolicySeverity.CRITICAL,
                    description="One or more safety checks have failed",
                    recommended_action=_governance_action_escalate(),
                )
            )

        if not context.get("audit_trail_intact", True):
            violations.append(
                PolicyViolation(
                    policy_id="builtin_audit_trail",
                    policy_name="Audit Trail Integrity",
                    severity=PolicySeverity.HIGH,
                    description="Audit trail integrity could not be verified",
                    recommended_action=_governance_action_escalate(),
                )
            )

        return violations


def _governance_action_escalate():
    """Helper to avoid circular import of GovernanceAction at module level."""
    from .models import GovernanceAction

    return GovernanceAction.ESCALATE
