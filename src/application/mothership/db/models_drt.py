"""DRT (Distributed Request Tracking) database models.

Provides database persistence for behavioral signatures, attack vectors,
and escalation history.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .models_base import Base, utcnow


class DRTBehavioralSignatureRow(Base):
    """Database model for behavioral signatures.

    Stores signatures of normal request patterns for comparison against attack vectors.
    """

    __tablename__ = "drt_behavioral_signatures"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    path_pattern: Mapped[str] = mapped_column(String(512), index=True)
    method: Mapped[str] = mapped_column(String(16), index=True)
    headers: Mapped[list[str]] = mapped_column(JSON, default=list)
    body_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    query_pattern: Mapped[str | None] = mapped_column(String(512), nullable=True)
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    retention_hours: Mapped[int] = mapped_column(Integer, default=96)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    violations: Mapped[list[DRTViolationRow]] = relationship(
        "DRTViolationRow", back_populates="signature", cascade="all, delete-orphan"
    )

    # Composite indexes for efficient queries
    __table_args__ = (
        Index("ix_drt_behavioral_signatures_path_method", "path_pattern", "method"),
        Index("ix_drt_behavioral_signatures_timestamp_retention", "timestamp", "retention_hours"),
    )


class DRTAttackVectorRow(Base):
    """Database model for attack vectors.

    Stores known attack patterns for behavioral similarity detection.
    """

    __tablename__ = "drt_attack_vectors"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    path_pattern: Mapped[str] = mapped_column(String(512), index=True)
    method: Mapped[str] = mapped_column(String(16), index=True)
    headers: Mapped[list[str]] = mapped_column(JSON, default=list)
    body_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    query_pattern: Mapped[str | None] = mapped_column(String(512), nullable=True)
    severity: Mapped[str] = mapped_column(String(32), default="medium")  # low, medium, high, critical
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    violations: Mapped[list[DRTViolationRow]] = relationship(
        "DRTViolationRow", back_populates="attack_vector", cascade="all, delete-orphan"
    )

    # Composite indexes
    __table_args__ = (
        Index("ix_drt_attack_vectors_path_method_active", "path_pattern", "method", "active"),
        Index("ix_drt_attack_vectors_severity_active", "severity", "active"),
    )


class DRTViolationRow(Base):
    """Database model for detected violations.

    Records when a behavioral signature matched an attack vector.
    """

    __tablename__ = "drt_violations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    signature_id: Mapped[str] = mapped_column(String(64), ForeignKey("drt_behavioral_signatures.id"), index=True)
    attack_vector_id: Mapped[str] = mapped_column(String(64), ForeignKey("drt_attack_vectors.id"), index=True)
    similarity_score: Mapped[float] = mapped_column(Float, default=0.0)
    request_path: Mapped[str] = mapped_column(String(512))
    request_method: Mapped[str] = mapped_column(String(16))
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    was_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    action_taken: Mapped[str] = mapped_column(String(64), default="escalate")  # escalate, block, log
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    signature: Mapped[DRTBehavioralSignatureRow] = relationship(
        "DRTBehavioralSignatureRow", back_populates="violations"
    )
    attack_vector: Mapped[DRTAttackVectorRow] = relationship("DRTAttackVectorRow", back_populates="violations")

    # Indexes for common queries
    __table_args__ = (
        Index("ix_drt_violations_timestamp_score", "timestamp", "similarity_score"),
        Index("ix_drt_violations_client_timestamp", "client_ip", "timestamp"),
    )


class DRTEscalatedEndpointRow(Base):
    """Database model for escalated endpoints.

    Tracks which endpoints are currently under elevated monitoring.
    """

    __tablename__ = "drt_escalated_endpoints"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    path: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    escalation_reason: Mapped[str] = mapped_column(String(256), default="behavioral_similarity")
    similarity_score: Mapped[float] = mapped_column(Float, default=0.0)
    matched_attack_vector_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("drt_attack_vectors.id"), nullable=True
    )
    escalation_count: Mapped[int] = mapped_column(Integer, default=1)
    last_violation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    attack_vector: Mapped[DRTAttackVectorRow | None] = relationship("DRTAttackVectorRow")

    __table_args__ = (
        Index("ix_drt_escalated_endpoints_active_expires", "is_active", "expires_at"),
        Index("ix_drt_escalated_endpoints_path_active", "path", "is_active"),
    )


class DRTFalsePositiveRow(Base):
    """Database model for tracking false positive violations.

    Allows users to mark violations as false positives and track patterns
    to improve detection accuracy over time.
    """

    __tablename__ = "drt_false_positives"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    violation_id: Mapped[str] = mapped_column(String(64), ForeignKey("drt_violations.id"), index=True)
    marked_by: Mapped[str | None] = mapped_column(String(256), nullable=True)  # User/system that marked it
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)  # Why it was marked as false positive
    confidence: Mapped[float] = mapped_column(Float, default=1.0)  # Confidence in false positive assessment
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    violation: Mapped[DRTViolationRow] = relationship("DRTViolationRow")

    __table_args__ = (
        Index("ix_drt_false_positives_created_at", "created_at"),
        Index("ix_drt_false_positives_violation_marked", "violation_id", "created_at"),
    )


class DRTFalsePositivePatternRow(Base):
    """Database model for patterns learned from false positives.

    Tracks recurring patterns that are consistently marked as false positives
    to automatically reduce false positive rates.
    """

    __tablename__ = "drt_false_positive_patterns"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    path_pattern: Mapped[str] = mapped_column(String(512), index=True)
    method: Mapped[str] = mapped_column(String(16), index=True)
    headers: Mapped[list[str]] = mapped_column(JSON, default=list)
    body_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    query_pattern: Mapped[str | None] = mapped_column(String(512), nullable=True)
    false_positive_count: Mapped[int] = mapped_column(Integer, default=1)
    total_violations: Mapped[int] = mapped_column(Integer, default=1)
    false_positive_rate: Mapped[float] = mapped_column(Float, default=1.0)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Composite indexes
    __table_args__ = (
        Index("ix_drt_false_positive_patterns_path_method", "path_pattern", "method", "active"),
        Index("ix_drt_false_positive_patterns_rate_active", "false_positive_rate", "active"),
    )


class DRTConfigurationRow(Base):
    """Database model for DRT configuration settings.

    Stores dynamic configuration that can be updated without restarting.
    """

    __tablename__ = "drt_configuration"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default="global")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    similarity_threshold: Mapped[float] = mapped_column(Float, default=0.85)
    retention_hours: Mapped[int] = mapped_column(Integer, default=96)
    websocket_overhead: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_escalate: Mapped[bool] = mapped_column(Boolean, default=True)
    escalation_timeout_minutes: Mapped[int] = mapped_column(Integer, default=60)
    rate_limit_multiplier: Mapped[float] = mapped_column(Float, default=0.5)
    sampling_rate: Mapped[float] = mapped_column(Float, default=1.0)
    alert_on_escalation: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
