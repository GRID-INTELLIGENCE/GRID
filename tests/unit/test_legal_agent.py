"""Unit tests for the GRID legal agent module."""

from __future__ import annotations

import pytest

from grid.legal import (
    AccountingBridge,
    ComplianceMonitor,
    ComplianceStatus,
    GovernanceAction,
    GovernanceEngine,
    GovernancePolicy,
    LegalAgent,
    PolicyDomain,
    PolicySeverity,
    UserRightsManager,
    UserRightType,
)

# ---------------------------------------------------------------------------
# Governance Engine
# ---------------------------------------------------------------------------


class TestGovernanceEngine:
    def test_default_policies_loaded(self) -> None:
        engine = GovernanceEngine()
        policies = engine.get_active_policies()
        assert len(policies) >= 6

    def test_register_custom_policy(self) -> None:
        engine = GovernanceEngine()
        policy = GovernancePolicy(
            name="Test Policy",
            description="A test governance policy",
            domain=PolicyDomain.CONTRACT,
            severity=PolicySeverity.LOW,
            conditions=["contract_signed"],
            prescribed_action=GovernanceAction.APPROVE,
        )
        engine.register_policy(policy)
        active = engine.get_active_policies(domain=PolicyDomain.CONTRACT)
        assert any(p.name == "Test Policy" for p in active)

    def test_deactivate_policy(self) -> None:
        engine = GovernanceEngine()
        policies = engine.get_active_policies()
        pid = policies[0].policy_id
        assert engine.deactivate_policy(pid) is True
        assert engine.deactivate_policy("nonexistent") is False
        assert all(p.policy_id != pid for p in engine.get_active_policies())

    def test_filter_by_domain(self) -> None:
        engine = GovernanceEngine()
        privacy = engine.get_active_policies(domain=PolicyDomain.DATA_PRIVACY)
        assert all(p.domain == PolicyDomain.DATA_PRIVACY for p in privacy)

    @pytest.mark.asyncio
    async def test_evaluate_compliant(self) -> None:
        engine = GovernanceEngine()
        context = {
            "has_user_consent": True,
            "within_retention_period": True,
            "accounting_notified": True,
            "non_discrimination_verified": True,
            "transparency_notice_provided": True,
            "safety_standards_met": True,
        }
        assessment = await engine.evaluate("test_target", context)
        assert assessment.status == ComplianceStatus.COMPLIANT
        assert assessment.score == 1.0
        assert len(assessment.violations) == 0

    @pytest.mark.asyncio
    async def test_evaluate_non_compliant(self) -> None:
        engine = GovernanceEngine()
        context = {"has_user_consent": False}
        assessment = await engine.evaluate("test_target", context)
        assert assessment.status == ComplianceStatus.NON_COMPLIANT
        assert len(assessment.violations) > 0
        assert assessment.score < 1.0

    @pytest.mark.asyncio
    async def test_evaluate_partial(self) -> None:
        engine = GovernanceEngine()
        # Satisfy critical policies, fail low-severity ones
        context = {
            "has_user_consent": True,
            "within_retention_period": True,
            "non_discrimination_verified": True,
            "safety_standards_met": True,
            # Missing: accounting_notified, transparency_notice_provided
        }
        assessment = await engine.evaluate("test_target", context)
        assert len(assessment.violations) > 0


# ---------------------------------------------------------------------------
# User Rights Manager
# ---------------------------------------------------------------------------


class TestUserRightsManager:
    @pytest.mark.asyncio
    async def test_submit_request(self) -> None:
        mgr = UserRightsManager()
        req = await mgr.submit_request(
            user_id="u1",
            right_type=UserRightType.ERASURE,
            description="Delete my data",
        )
        assert req.user_id == "u1"
        assert req.right_type == UserRightType.ERASURE
        assert req.status.value == "acknowledged"

    @pytest.mark.asyncio
    async def test_fulfill_request(self) -> None:
        mgr = UserRightsManager()
        req = await mgr.submit_request(user_id="u1", right_type=UserRightType.ACCESS)
        result = await mgr.fulfill_request(req.request_id, "Data exported")
        assert result is not None
        assert result.status.value == "fulfilled"
        assert result.resolved_at is not None

    @pytest.mark.asyncio
    async def test_deny_request(self) -> None:
        mgr = UserRightsManager()
        req = await mgr.submit_request(user_id="u1", right_type=UserRightType.ERASURE)
        result = await mgr.deny_request(req.request_id, "Legally required retention")
        assert result is not None
        assert result.status.value == "denied"

    @pytest.mark.asyncio
    async def test_escalate_request(self) -> None:
        mgr = UserRightsManager()
        req = await mgr.submit_request(user_id="u1", right_type=UserRightType.OBJECTION)
        result = await mgr.escalate_request(req.request_id, "Needs legal counsel")
        assert result is not None
        assert result.status.value == "escalated"

    @pytest.mark.asyncio
    async def test_fulfill_unknown_returns_none(self) -> None:
        mgr = UserRightsManager()
        assert await mgr.fulfill_request("nope", "x") is None

    @pytest.mark.asyncio
    async def test_get_pending_requests(self) -> None:
        mgr = UserRightsManager()
        await mgr.submit_request(user_id="u1", right_type=UserRightType.ACCESS)
        await mgr.submit_request(user_id="u2", right_type=UserRightType.PORTABILITY)
        pending = mgr.get_pending_requests(user_id="u1")
        assert len(pending) == 1
        assert pending[0].user_id == "u1"

    @pytest.mark.asyncio
    async def test_wellbeing_high_interaction(self) -> None:
        mgr = UserRightsManager()
        flags = await mgr.check_wellbeing("u1", {"interaction_density_score": 0.95})
        assert len(flags) >= 1
        assert any("interaction density" in f.concern.lower() for f in flags)

    @pytest.mark.asyncio
    async def test_wellbeing_high_cognitive_load(self) -> None:
        mgr = UserRightsManager()
        flags = await mgr.check_wellbeing("u1", {"cognitive_load_level": "critical"})
        assert len(flags) >= 1

    @pytest.mark.asyncio
    async def test_wellbeing_extended_session(self) -> None:
        mgr = UserRightsManager()
        flags = await mgr.check_wellbeing("u1", {"hours_active_today": 12})
        assert len(flags) >= 1

    @pytest.mark.asyncio
    async def test_resolve_wellbeing_flag(self) -> None:
        mgr = UserRightsManager()
        flag = await mgr.raise_wellbeing_flag(
            user_id="u1",
            concern="Test concern",
            severity=PolicySeverity.MEDIUM,
            source="test",
        )
        resolved = await mgr.resolve_wellbeing_flag(flag.flag_id)
        assert resolved is not None
        assert resolved.resolved is True
        assert len(mgr.get_active_wellbeing_flags()) == 0


# ---------------------------------------------------------------------------
# Compliance Monitor
# ---------------------------------------------------------------------------


class TestComplianceMonitor:
    @pytest.mark.asyncio
    async def test_full_check_compliant(self) -> None:
        gov = GovernanceEngine()
        rights = UserRightsManager()
        monitor = ComplianceMonitor(gov, rights)

        assessment = await monitor.run_full_check(
            target="pipeline_x",
            context={
                "has_user_consent": True,
                "within_retention_period": True,
                "accounting_notified": True,
                "non_discrimination_verified": True,
                "transparency_notice_provided": True,
                "safety_standards_met": True,
            },
        )
        assert assessment.status == ComplianceStatus.COMPLIANT

    @pytest.mark.asyncio
    async def test_safety_boundary_violations(self) -> None:
        gov = GovernanceEngine()
        rights = UserRightsManager()
        monitor = ComplianceMonitor(gov, rights)

        violations = await monitor.check_safety_boundaries({"boundary_engine_active": False})
        assert len(violations) >= 1
        assert any("Boundary engine" in v.description for v in violations)

    @pytest.mark.asyncio
    async def test_audit_trail_violation(self) -> None:
        gov = GovernanceEngine()
        rights = UserRightsManager()
        monitor = ComplianceMonitor(gov, rights)

        violations = await monitor.check_safety_boundaries({"audit_trail_intact": False})
        assert any("Audit trail" in v.description for v in violations)


# ---------------------------------------------------------------------------
# Accounting Bridge
# ---------------------------------------------------------------------------


class TestAccountingBridge:
    @pytest.mark.asyncio
    async def test_send_message_local(self) -> None:
        bridge = AccountingBridge()
        msg = await bridge.notify_compliance_cost(
            subject="GDPR training",
            amount=5000.0,
        )
        assert msg.amount == 5000.0
        assert len(bridge.get_outbox()) == 1

    @pytest.mark.asyncio
    async def test_notify_penalty_risk(self) -> None:
        bridge = AccountingBridge()
        msg = await bridge.notify_penalty_risk(
            subject="Potential GDPR fine",
            estimated_amount=50000.0,
        )
        assert msg.requires_response is True

    @pytest.mark.asyncio
    async def test_request_audit(self) -> None:
        bridge = AccountingBridge()
        msg = await bridge.request_audit(subject="Q4 compliance audit")
        assert msg.requires_response is True

    @pytest.mark.asyncio
    async def test_pending_responses(self) -> None:
        bridge = AccountingBridge()
        await bridge.notify_penalty_risk(subject="Test", estimated_amount=100.0)
        pending = bridge.get_pending_responses()
        assert len(pending) == 1

    @pytest.mark.asyncio
    async def test_receive_message(self) -> None:
        from grid.legal.models import AccountingEventType, AccountingMessage

        bridge = AccountingBridge()
        msg = AccountingMessage(
            event_type=AccountingEventType.AUDIT_REQUEST,
            subject="Audit response",
        )
        await bridge.receive_message(msg)
        assert len(bridge.get_inbox()) == 1


# ---------------------------------------------------------------------------
# Legal Agent (orchestrator)
# ---------------------------------------------------------------------------


class TestLegalAgent:
    @pytest.mark.asyncio
    async def test_conduct_review_compliant(self) -> None:
        agent = LegalAgent()
        review = await agent.conduct_review(
            case_id="case_001",
            target="clean_pipeline",
            context={
                "has_user_consent": True,
                "within_retention_period": True,
                "accounting_notified": True,
                "non_discrimination_verified": True,
                "transparency_notice_provided": True,
                "safety_standards_met": True,
            },
            user_id="u1",
        )
        assert review.overall_status == ComplianceStatus.COMPLIANT
        assert len(review.violations) == 0

    @pytest.mark.asyncio
    async def test_conduct_review_with_violations(self) -> None:
        agent = LegalAgent()
        review = await agent.conduct_review(
            case_id="case_002",
            target="risky_pipeline",
            context={"has_user_consent": False},
        )
        assert review.overall_status == ComplianceStatus.NON_COMPLIANT
        assert len(review.violations) > 0
        assert review.summary != ""

    @pytest.mark.asyncio
    async def test_conduct_review_with_wellbeing_flags(self) -> None:
        agent = LegalAgent()
        review = await agent.conduct_review(
            case_id="case_003",
            target="user_session",
            context={
                "has_user_consent": True,
                "within_retention_period": True,
                "accounting_notified": True,
                "non_discrimination_verified": True,
                "transparency_notice_provided": True,
                "safety_standards_met": True,
                "interaction_density_score": 0.95,
            },
            user_id="u2",
        )
        assert len(review.wellbeing_flags) >= 1
        assert review.overall_status == ComplianceStatus.PARTIALLY_COMPLIANT

    @pytest.mark.asyncio
    async def test_conduct_review_safety_boundary_failure(self) -> None:
        agent = LegalAgent()
        review = await agent.conduct_review(
            case_id="case_004",
            target="boundary_test",
            context={
                "has_user_consent": True,
                "within_retention_period": True,
                "accounting_notified": True,
                "non_discrimination_verified": True,
                "transparency_notice_provided": True,
                "safety_standards_met": True,
                "boundary_engine_active": False,
            },
        )
        assert review.overall_status == ComplianceStatus.NON_COMPLIANT

    @pytest.mark.asyncio
    async def test_handle_user_right_request(self) -> None:
        agent = LegalAgent()
        request_id = await agent.handle_user_right_request(
            case_id="case_005",
            user_id="u3",
            right_type=UserRightType.ERASURE,
            description="Remove all my data",
        )
        assert request_id.startswith("urr_")

    @pytest.mark.asyncio
    async def test_fulfill_user_right(self) -> None:
        agent = LegalAgent()
        request_id = await agent.handle_user_right_request(
            case_id="case_006",
            user_id="u4",
            right_type=UserRightType.ACCESS,
        )
        fulfilled = await agent.fulfill_user_right("case_006", request_id, "Data exported")
        assert fulfilled is True

    @pytest.mark.asyncio
    async def test_fulfill_unknown_request(self) -> None:
        agent = LegalAgent()
        assert await agent.fulfill_user_right("case_x", "nope", "x") is False

    @pytest.mark.asyncio
    async def test_request_accounting_audit(self) -> None:
        agent = LegalAgent()
        msg_id = await agent.request_accounting_audit(
            case_id="case_007",
            subject="Quarterly compliance",
        )
        assert msg_id.startswith("acm_")

    @pytest.mark.asyncio
    async def test_accounting_notified_on_violations(self) -> None:
        agent = LegalAgent()
        await agent.conduct_review(
            case_id="case_008",
            target="violation_pipeline",
            context={"has_user_consent": False},
        )
        outbox = agent.accounting.get_outbox()
        assert len(outbox) >= 1
