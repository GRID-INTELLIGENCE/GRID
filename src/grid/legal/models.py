"""Domain models for the legal agent.

Covers governance policies, compliance assessments, user rights,
and accounting integration data structures.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PolicyDomain(str, Enum):
    """Business domains a governance policy can target."""

    DATA_PRIVACY = "data_privacy"
    EMPLOYMENT = "employment"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    CONTRACT = "contract"
    REGULATORY = "regulatory"
    FINANCIAL = "financial"
    CONSUMER_PROTECTION = "consumer_protection"
    HEALTH_SAFETY = "health_safety"


class PolicySeverity(str, Enum):
    """Severity classification for policy violations."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStatus(str, Enum):
    """Overall compliance posture."""

    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    UNDER_REVIEW = "under_review"
    REMEDIATION_IN_PROGRESS = "remediation_in_progress"


class UserRightType(str, Enum):
    """Recognised user rights categories."""

    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    PORTABILITY = "portability"
    OBJECTION = "objection"
    RESTRICTION = "restriction"
    CONSENT_WITHDRAWAL = "consent_withdrawal"
    NON_DISCRIMINATION = "non_discrimination"
    WELLBEING_PROTECTION = "wellbeing_protection"
    TRANSPARENCY = "transparency"


class UserRightRequestStatus(str, Enum):
    """Lifecycle of a user-right request."""

    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    FULFILLED = "fulfilled"
    DENIED = "denied"
    ESCALATED = "escalated"


class AccountingEventType(str, Enum):
    """Types of events the legal agent exchanges with accounting."""

    COMPLIANCE_COST = "compliance_cost"
    PENALTY_RISK = "penalty_risk"
    AUDIT_REQUEST = "audit_request"
    POLICY_BUDGET = "policy_budget"
    INVOICE_REVIEW = "invoice_review"
    TAX_OBLIGATION = "tax_obligation"


class GovernanceAction(str, Enum):
    """Actions the governance engine can prescribe."""

    APPROVE = "approve"
    DENY = "deny"
    ESCALATE = "escalate"
    REQUIRE_REVIEW = "require_review"
    REQUIRE_CONSENT = "require_consent"
    LOG_ONLY = "log_only"
    REMEDIATE = "remediate"


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------


class GovernancePolicy(BaseModel):
    """A single governance policy enforced by the legal agent."""

    policy_id: str = Field(default_factory=lambda: f"pol_{uuid.uuid4().hex[:12]}")
    name: str
    description: str
    domain: PolicyDomain
    severity: PolicySeverity = PolicySeverity.MEDIUM
    enforcement: str = "hard"  # hard | soft | audit
    conditions: list[str] = Field(default_factory=list)
    prescribed_action: GovernanceAction = GovernanceAction.REQUIRE_REVIEW
    effective_from: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    active: bool = True


class PolicyViolation(BaseModel):
    """A detected violation against a governance policy."""

    violation_id: str = Field(default_factory=lambda: f"vio_{uuid.uuid4().hex[:12]}")
    policy_id: str
    policy_name: str
    severity: PolicySeverity
    description: str
    evidence: list[str] = Field(default_factory=list)
    recommended_action: GovernanceAction = GovernanceAction.REMEDIATE
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved: bool = False
    resolution_notes: str = ""


class ComplianceAssessment(BaseModel):
    """Result of a compliance check across one or more policies."""

    assessment_id: str = Field(default_factory=lambda: f"ca_{uuid.uuid4().hex[:12]}")
    target: str  # what was assessed (e.g. "user_data_pipeline")
    status: ComplianceStatus = ComplianceStatus.UNDER_REVIEW
    policies_checked: list[str] = Field(default_factory=list)
    violations: list[PolicyViolation] = Field(default_factory=list)
    score: float = 1.0  # 0.0 = fully non-compliant, 1.0 = fully compliant
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    next_review: datetime | None = None
    assessor: str = "legal_agent"
    notes: str = ""


class UserRightRequest(BaseModel):
    """A user exercising one of their recognised rights."""

    request_id: str = Field(default_factory=lambda: f"urr_{uuid.uuid4().hex[:12]}")
    user_id: str
    right_type: UserRightType
    status: UserRightRequestStatus = UserRightRequestStatus.PENDING
    description: str = ""
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    resolution_summary: str = ""
    priority: PolicySeverity = PolicySeverity.MEDIUM
    metadata: dict[str, Any] = Field(default_factory=dict)


class WellbeingFlag(BaseModel):
    """A flag raised by the legal agent when user wellbeing is at risk."""

    flag_id: str = Field(default_factory=lambda: f"wbf_{uuid.uuid4().hex[:12]}")
    user_id: str
    concern: str
    severity: PolicySeverity
    source: str  # which subsystem raised it
    raised_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    mitigations: list[str] = Field(default_factory=list)
    resolved: bool = False


class AccountingMessage(BaseModel):
    """Asynchronous message exchanged with the accounting department."""

    message_id: str = Field(default_factory=lambda: f"acm_{uuid.uuid4().hex[:12]}")
    event_type: AccountingEventType
    subject: str
    amount: float | None = None
    currency: str = "USD"
    user_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str | None = None
    requires_response: bool = False


class LegalReview(BaseModel):
    """Aggregate legal review produced by the agent."""

    review_id: str = Field(default_factory=lambda: f"lr_{uuid.uuid4().hex[:12]}")
    case_id: str
    assessments: list[ComplianceAssessment] = Field(default_factory=list)
    violations: list[PolicyViolation] = Field(default_factory=list)
    user_right_requests: list[UserRightRequest] = Field(default_factory=list)
    wellbeing_flags: list[WellbeingFlag] = Field(default_factory=list)
    accounting_messages: list[AccountingMessage] = Field(default_factory=list)
    overall_status: ComplianceStatus = ComplianceStatus.UNDER_REVIEW
    summary: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
