"""Core legal agent orchestrator.

The ``LegalAgent`` ties together governance, compliance, user-rights,
and accounting into a single async-first agent that can be embedded in the
GRID agentic workflow.  It publishes legal-domain events to both the local
agentic ``EventBus`` and the unified-fabric ``DynamicEventBus``.
"""

from __future__ import annotations

import logging
from typing import Any

from .accounting_bridge import AccountingBridge
from .compliance import ComplianceMonitor
from .events import (
    AccountingMessageSentEvent,
    LegalReviewCompletedEvent,
    LegalReviewStartedEvent,
    PolicyEvaluatedEvent,
    PolicyViolationDetectedEvent,
    UserRightFulfilledEvent,
    UserRightRequestedEvent,
    WellbeingConcernRaisedEvent,
)
from .governance import GovernanceEngine
from .models import (
    AccountingEventType,
    ComplianceStatus,
    LegalReview,
    PolicyDomain,
    PolicySeverity,
    UserRightType,
)
from .user_rights import UserRightsManager

logger = logging.getLogger(__name__)


class LegalAgent:
    """Asynchronous legal agent for GRID.

    Responsibilities:
    - Governance policy evaluation and enforcement
    - Compliance monitoring (continuous and on-demand)
    - User-right request management and wellbeing protection
    - Async communication with the accounting department
    - Integration with safety / security / boundary layers
    """

    def __init__(
        self,
        event_bus: Any | None = None,
        unified_event_bus: Any | None = None,
    ) -> None:
        self.governance = GovernanceEngine()
        self.user_rights = UserRightsManager()
        self.compliance = ComplianceMonitor(self.governance, self.user_rights)
        self.accounting = AccountingBridge()

        # Local agentic event bus (grid.agentic.event_bus)
        self._event_bus = event_bus
        # Unified fabric DynamicEventBus
        self._unified_bus = unified_event_bus

        if unified_event_bus is not None:
            self.accounting.connect_event_bus(unified_event_bus)

    # -- Full legal review ---------------------------------------------------

    async def conduct_review(
        self,
        case_id: str,
        target: str,
        context: dict[str, Any],
        user_id: str | None = None,
        domains: list[PolicyDomain] | None = None,
    ) -> LegalReview:
        """Run a comprehensive legal review for *case_id*.

        This is the primary entry point.  It:
        1. Evaluates governance policies
        2. Checks safety/boundary compliance
        3. Runs wellbeing checks (when a user_id is provided)
        4. Notifies accounting of any financial implications
        5. Publishes events throughout the lifecycle
        """
        await self._emit(LegalReviewStartedEvent(case_id=case_id, target=target))

        # 1. Governance + compliance
        assessment = await self.compliance.run_full_check(
            target=target,
            context=context,
            user_id=user_id,
            domains=domains,
        )

        await self._emit(
            PolicyEvaluatedEvent(
                case_id=case_id,
                policies_checked=len(assessment.policies_checked),
                violations_found=len(assessment.violations),
                compliance_score=assessment.score,
            )
        )

        for v in assessment.violations:
            await self._emit(
                PolicyViolationDetectedEvent(
                    case_id=case_id,
                    violation_id=v.violation_id,
                    policy_id=v.policy_id,
                    severity=v.severity.value,
                    description=v.description,
                )
            )

        # 2. Safety / boundary checks
        safety_violations = await self.compliance.check_safety_boundaries(context)
        all_violations = list(assessment.violations) + safety_violations

        # 3. Wellbeing checks
        wellbeing_flags = []
        if user_id:
            wellbeing_flags = await self.user_rights.check_wellbeing(user_id, context)
            for flag in wellbeing_flags:
                await self._emit(
                    WellbeingConcernRaisedEvent(
                        case_id=case_id,
                        flag_id=flag.flag_id,
                        user_id=user_id,
                        concern=flag.concern,
                        severity=flag.severity.value,
                    )
                )

        # 4. Accounting notifications for financial implications
        accounting_messages = []
        critical_count = sum(1 for v in all_violations if v.severity in (PolicySeverity.HIGH, PolicySeverity.CRITICAL))
        if critical_count > 0:
            msg = await self.accounting.notify_penalty_risk(
                subject=f"Legal review for '{target}' found {critical_count} high/critical violation(s)",
                estimated_amount=0.0,  # actual estimates require domain-specific logic
                details={"case_id": case_id, "violation_count": critical_count},
            )
            accounting_messages.append(msg)
            await self._emit(
                AccountingMessageSentEvent(
                    case_id=case_id,
                    message_id=msg.message_id,
                    accounting_event_type=msg.event_type.value,
                    subject=msg.subject,
                )
            )

        # 5. Build review
        overall = self._derive_overall_status(assessment.status, safety_violations, wellbeing_flags)
        review = LegalReview(
            case_id=case_id,
            assessments=[assessment],
            violations=all_violations,
            wellbeing_flags=wellbeing_flags,
            accounting_messages=accounting_messages,
            overall_status=overall,
            summary=self._build_summary(target, assessment, all_violations, wellbeing_flags),
        )

        await self._emit(
            LegalReviewCompletedEvent(
                case_id=case_id,
                review_id=review.review_id,
                overall_status=overall.value,
                total_violations=len(all_violations),
                compliance_score=assessment.score,
                summary=review.summary,
            )
        )

        logger.info(
            "legal_review_complete",
            extra={
                "case_id": case_id,
                "review_id": review.review_id,
                "status": overall.value,
                "violations": len(all_violations),
            },
        )
        return review

    # -- User-right request delegation ---------------------------------------

    async def handle_user_right_request(
        self,
        case_id: str,
        user_id: str,
        right_type: UserRightType,
        description: str = "",
    ) -> str:
        """Submit and acknowledge a user-right request, returning the request id."""
        request = await self.user_rights.submit_request(
            user_id=user_id,
            right_type=right_type,
            description=description,
        )
        await self._emit(
            UserRightRequestedEvent(
                case_id=case_id,
                request_id=request.request_id,
                user_id=user_id,
                right_type=right_type.value,
            )
        )
        return request.request_id

    async def fulfill_user_right(
        self,
        case_id: str,
        request_id: str,
        resolution_summary: str,
    ) -> bool:
        """Fulfill a previously submitted user-right request."""
        request = await self.user_rights.fulfill_request(request_id, resolution_summary)
        if request is None:
            return False
        await self._emit(
            UserRightFulfilledEvent(
                case_id=case_id,
                request_id=request.request_id,
                user_id=request.user_id,
                right_type=request.right_type.value,
                resolution=resolution_summary,
            )
        )
        return True

    # -- Accounting convenience methods --------------------------------------

    async def request_accounting_audit(
        self,
        case_id: str,
        subject: str,
        details: dict[str, Any] | None = None,
    ) -> str:
        """Ask the accounting department for an audit."""
        msg = await self.accounting.request_audit(subject=subject, details=details)
        await self._emit(
            AccountingMessageSentEvent(
                case_id=case_id,
                message_id=msg.message_id,
                accounting_event_type=AccountingEventType.AUDIT_REQUEST.value,
                subject=subject,
            )
        )
        return msg.message_id

    # -- Helpers -------------------------------------------------------------

    @staticmethod
    def _derive_overall_status(
        assessment_status: ComplianceStatus,
        safety_violations: list[Any],
        wellbeing_flags: list[Any],
    ) -> ComplianceStatus:
        if safety_violations:
            return ComplianceStatus.NON_COMPLIANT
        if wellbeing_flags:
            if assessment_status == ComplianceStatus.COMPLIANT:
                return ComplianceStatus.PARTIALLY_COMPLIANT
            return assessment_status
        return assessment_status

    @staticmethod
    def _build_summary(
        target: str,
        assessment: Any,
        violations: list[Any],
        wellbeing_flags: list[Any],
    ) -> str:
        parts = [f"Legal review of '{target}':"]
        parts.append(f"  Policies checked: {len(assessment.policies_checked)}")
        parts.append(f"  Violations: {len(violations)}")
        parts.append(f"  Compliance score: {assessment.score:.2f}")
        if wellbeing_flags:
            parts.append(f"  Wellbeing concerns: {len(wellbeing_flags)}")
        return "\n".join(parts)

    async def _emit(self, event: Any) -> None:
        """Publish an event to attached buses (best-effort)."""
        if self._event_bus is not None:
            try:
                await self._event_bus.publish(event)
            except Exception:
                logger.debug("local_event_bus_publish_failed", exc_info=True)

        if self._unified_bus is not None:
            try:
                from unified_fabric import Event as FabricEvent

                fabric_event = FabricEvent(
                    event_type=event.event_type,
                    payload=event.to_dict(),
                    source_domain="grid",
                    target_domains=["grid", "safety"],
                )
                await self._unified_bus.publish(fabric_event)
            except Exception:
                logger.debug("unified_bus_publish_failed", exc_info=True)
