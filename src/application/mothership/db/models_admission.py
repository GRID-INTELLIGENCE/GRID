"""SQLAlchemy models for admission gate entity persistence.

Persists EntityRecord and EntityViolation across Mothership restarts.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .models_base import Base, utcnow


class AdmissionEntityRow(Base):
    """Persisted entity record — mirrors EntityRecord from admission_gate.py."""

    __tablename__ = "admission_entities"

    entity_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    total_penalty_points: Mapped[int] = mapped_column(Integer, default=0)
    bannered: Mapped[bool] = mapped_column(Boolean, default=False)
    banner_reason: Mapped[str] = mapped_column(String(512), default="")
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    violations: Mapped[list[AdmissionViolationRow]] = relationship(
        back_populates="entity", cascade="all, delete-orphan", lazy="selectin",
    )


class AdmissionViolationRow(Base):
    """Persisted violation record — mirrors EntityViolation from admission_gate.py."""

    __tablename__ = "admission_violations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[str] = mapped_column(
        String(256), ForeignKey("admission_entities.entity_id", ondelete="CASCADE"), index=True,
    )
    violation_type: Mapped[str] = mapped_column(String(64), index=True)
    penalty_points: Mapped[int] = mapped_column(Integer)
    violation_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    entity: Mapped[AdmissionEntityRow] = relationship(back_populates="violations")
