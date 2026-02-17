"""SQLAlchemy models for agentic system."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Float, String, Text

from .models_base import Base

logger = __import__("logging").getLogger(__name__)


class AgenticCase(Base):
    """Model for agentic cases stored in Databricks."""

    __tablename__ = "agentic_cases"

    # Primary key
    case_id = Column(String(255), primary_key=True, comment="Unique case identifier")

    # Input data
    raw_input = Column(Text, nullable=False, comment="Original raw user input")
    user_id = Column(String(255), nullable=True, comment="User identifier")

    # Categorization
    category = Column(String(100), nullable=True, comment="Case category")
    priority = Column(String(50), nullable=True, default="medium", comment="Case priority")
    confidence = Column(Float, nullable=True, comment="Classification confidence score")

    # Structured data (JSON)
    structured_data = Column(JSON, nullable=True, comment="Structured case data from filing system")
    labels = Column(JSON, nullable=True, comment="Case labels")
    keywords = Column(JSON, nullable=True, comment="Extracted keywords")
    entities = Column(JSON, nullable=True, comment="Extracted entities")
    relationships = Column(JSON, nullable=True, comment="Detected relationships")

    # Reference file
    reference_file_path = Column(String(500), nullable=True, comment="Path to reference file")

    # Status tracking
    status = Column(
        String(50),
        nullable=False,
        default="created",
        comment="Case status: created, categorized, reference_generated, executed, completed",
    )

    # Execution data
    agent_role = Column(String(100), nullable=True, comment="Agent role used for execution")
    task = Column(String(100), nullable=True, comment="Task executed")

    # Outcome
    outcome = Column(
        String(50),
        nullable=True,
        comment="Case outcome: success, partial, failure",
    )
    solution = Column(Text, nullable=True, comment="Solution applied")
    agent_experience = Column(JSON, nullable=True, comment="Agent experience data")

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), comment="Case creation timestamp")
    updated_at = Column(DateTime, nullable=True, onupdate=lambda: datetime.now(UTC), comment="Last update timestamp")
    completed_at = Column(DateTime, nullable=True, comment="Completion timestamp")

    # Execution metrics
    execution_time_seconds = Column(Float, nullable=True, comment="Execution time in seconds")

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "case_id": self.case_id,
            "raw_input": self.raw_input,
            "user_id": self.user_id,
            "category": self.category,
            "priority": self.priority,
            "confidence": self.confidence,
            "structured_data": self.structured_data,
            "labels": self.labels,
            "keywords": self.keywords,
            "entities": self.entities,
            "relationships": self.relationships,
            "reference_file_path": self.reference_file_path,
            "status": self.status,
            "agent_role": self.agent_role,
            "task": self.task,
            "outcome": self.outcome,
            "solution": self.solution,
            "agent_experience": self.agent_experience,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time_seconds": self.execution_time_seconds,
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"<AgenticCase(case_id={self.case_id}, status={self.status}, category={self.category})>"
