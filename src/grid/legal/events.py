"""Event definitions for the legal agent domain.

All events follow the same dataclass pattern used by the agentic system
(see ``grid.agentic.events``) so they integrate cleanly with both the
local ``EventBus`` and the ``unified_fabric`` ``DynamicEventBus``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class BaseLegalEvent:
    """Base class for all legal-domain events."""

    case_id: str
    event_type: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "case_id": self.case_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


# -- Governance events -------------------------------------------------------


@dataclass
class PolicyEvaluatedEvent(BaseLegalEvent):
    """Fired after the governance engine evaluates policies for a case."""

    policies_checked: int = 0
    violations_found: int = 0
    compliance_score: float = 1.0
    event_type: str = field(default="legal.policy.evaluated")

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "policies_checked": self.policies_checked,
                "violations_found": self.violations_found,
                "compliance_score": self.compliance_score,
            }
        )
        return base


@dataclass
class PolicyViolationDetectedEvent(BaseLegalEvent):
    """Fired when a specific policy violation is detected."""

    violation_id: str = ""
    policy_id: str = ""
    severity: str = "medium"
    description: str = ""
    event_type: str = field(default="legal.policy.violation_detected")

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "violation_id": self.violation_id,
                "policy_id": self.policy_id,
                "severity": self.severity,
                "description": self.description,
            }
        )
        return base


# -- User rights events ------------------------------------------------------


@dataclass
class UserRightRequestedEvent(BaseLegalEvent):
    """Fired when a user exercises a legal right."""

    request_id: str = ""
    user_id: str = ""
    right_type: str = ""
    event_type: str = field(default="legal.user_right.requested")

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "request_id": self.request_id,
                "user_id": self.user_id,
                "right_type": self.right_type,
            }
        )
        return base


@dataclass
class UserRightFulfilledEvent(BaseLegalEvent):
    """Fired when a user-right request has been fulfilled."""

    request_id: str = ""
    user_id: str = ""
    right_type: str = ""
    resolution: str = ""
    event_type: str = field(default="legal.user_right.fulfilled")

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "request_id": self.request_id,
                "user_id": self.user_id,
                "right_type": self.right_type,
                "resolution": self.resolution,
            }
        )
        return base


# -- Wellbeing events --------------------------------------------------------


@dataclass
class WellbeingConcernRaisedEvent(BaseLegalEvent):
    """Fired when the legal agent identifies a user-wellbeing risk."""

    flag_id: str = ""
    user_id: str = ""
    concern: str = ""
    severity: str = "medium"
    event_type: str = field(default="legal.wellbeing.concern_raised")

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "flag_id": self.flag_id,
                "user_id": self.user_id,
                "concern": self.concern,
                "severity": self.severity,
            }
        )
        return base


# -- Accounting integration events -------------------------------------------


@dataclass
class AccountingMessageSentEvent(BaseLegalEvent):
    """Fired when the legal agent sends a message to accounting."""

    message_id: str = ""
    accounting_event_type: str = ""
    subject: str = ""
    amount: float | None = None
    event_type: str = field(default="legal.accounting.message_sent")

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "message_id": self.message_id,
                "accounting_event_type": self.accounting_event_type,
                "subject": self.subject,
                "amount": self.amount,
            }
        )
        return base


# -- Review lifecycle events -------------------------------------------------


@dataclass
class LegalReviewStartedEvent(BaseLegalEvent):
    """Fired when a full legal review begins."""

    target: str = ""
    event_type: str = field(default="legal.review.started")

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["target"] = self.target
        return base


@dataclass
class LegalReviewCompletedEvent(BaseLegalEvent):
    """Fired when a full legal review is finalised."""

    review_id: str = ""
    overall_status: str = "under_review"
    total_violations: int = 0
    compliance_score: float = 1.0
    summary: str = ""
    event_type: str = field(default="legal.review.completed")

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "review_id": self.review_id,
                "overall_status": self.overall_status,
                "total_violations": self.total_violations,
                "compliance_score": self.compliance_score,
                "summary": self.summary,
            }
        )
        return base
