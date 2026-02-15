"""
SQLAlchemy ORM models for the safety audit database.

Table: audits
Indexes: request_id, user_id, created_at

PII Redaction: User input is automatically redacted before storage
to prevent PII leakage in audit logs. See `redact_pii()`.
"""

from __future__ import annotations

import enum
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Index,
    String,
    Text,
    event,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ---------------------------------------------------------------------------
# PII Redaction
# ---------------------------------------------------------------------------
_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Email addresses
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "[REDACTED_EMAIL]"),
    # Phone numbers (international + US formats)
    (re.compile(r"\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}"), "[REDACTED_PHONE]"),
    # SSN (US)
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    # Credit card numbers (basic)
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "[REDACTED_CARD]"),
    # IP addresses
    (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "[REDACTED_IP]"),
]


def redact_pii(text: str | None) -> str | None:
    """Redact common PII patterns from text before audit storage."""
    if not text:
        return text
    result = text
    for pattern, replacement in _PII_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


class Base(DeclarativeBase):
    """Declarative base for audit models."""

    pass


class Severity(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditStatus(enum.StrEnum):
    OPEN = "open"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class TrustTier(enum.StrEnum):
    ANON = "anon"
    USER = "user"
    VERIFIED = "verified"
    PRIVILEGED = "privileged"


class AuditRecord(Base):
    """
    Primary audit table for the safety enforcement pipeline.

    Every refusal, escalation, and resolution is recorded here.
    """

    __tablename__ = "audits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    trust_tier: Mapped[TrustTier] = mapped_column(Enum(TrustTier), nullable=False)
    input: Mapped[str] = mapped_column(Text, nullable=False)
    model_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    detector_scores: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), nullable=False, default=Severity.LOW)
    status: Mapped[AuditStatus] = mapped_column(Enum(AuditStatus), nullable=False, default=AuditStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (Index("ix_audits_request_user_created", "request_id", "user_id", "created_at"),)

    def __repr__(self) -> str:
        return (
            f"<AuditRecord id={self.id} request_id={self.request_id} "
            f"reason={self.reason_code} status={self.status.value}>"
        )


# Auto-redact PII before any AuditRecord is persisted.
@event.listens_for(AuditRecord, "before_insert")
def _redact_audit_pii(mapper, connection, target: AuditRecord) -> None:  # noqa: ARG001
    """Automatically redact PII from input/output fields before DB insert."""
    target.input = redact_pii(target.input) or ""
    target.model_output = redact_pii(target.model_output)
