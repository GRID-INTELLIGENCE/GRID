"""GRID Legal Agent — governance, compliance, user-rights, and accounting.

Usage::

    from grid.legal import LegalAgent

    agent = LegalAgent()
    review = await agent.conduct_review(
        case_id="case_001",
        target="user_data_pipeline",
        context={"has_user_consent": True, "within_retention_period": True},
        user_id="user_42",
    )
"""

from .accounting_bridge import AccountingBridge
from .agent import LegalAgent
from .compliance import ComplianceMonitor
from .governance import GovernanceEngine
from .models import (
    AccountingEventType,
    AccountingMessage,
    ComplianceAssessment,
    ComplianceStatus,
    GovernanceAction,
    GovernancePolicy,
    LegalReview,
    PolicyDomain,
    PolicySeverity,
    PolicyViolation,
    UserRightRequest,
    UserRightRequestStatus,
    UserRightType,
    WellbeingFlag,
)
from .user_rights import UserRightsManager

__all__ = [
    "AccountingBridge",
    "AccountingEventType",
    "AccountingMessage",
    "ComplianceAssessment",
    "ComplianceMonitor",
    "ComplianceStatus",
    "GovernanceAction",
    "GovernanceEngine",
    "GovernancePolicy",
    "LegalAgent",
    "LegalReview",
    "PolicyDomain",
    "PolicySeverity",
    "PolicyViolation",
    "UserRightRequest",
    "UserRightRequestStatus",
    "UserRightType",
    "UserRightsManager",
    "WellbeingFlag",
]
