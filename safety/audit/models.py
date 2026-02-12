"""
SQLAlchemy ORM models for the safety audit database.

Table: audits
Indexes: request_id, user_id, created_at
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for audit models."""

    pass


class Severity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditStatus(str, enum.Enum):
    OPEN = "open"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class TrustTier(str, enum.Enum):
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
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity), nullable=False, default=Severity.LOW
    )
    status: Mapped[AuditStatus] = mapped_column(
        Enum(AuditStatus), nullable=False, default=AuditStatus.OPEN
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewer_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        Index("ix_audits_request_user_created", "request_id", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditRecord id={self.id} request_id={self.request_id} "
            f"reason={self.reason_code} status={self.status.value}>"
        )
