"""Event definitions for agentic system."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class BaseEvent(ABC):
    """Base event class for all agentic system events."""

    case_id: str
    event_type: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "case_id": self.case_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class CaseCreatedEvent(BaseEvent):
    """Event emitted when a case is created (receptionist receives input)."""

    raw_input: str = ""
    user_id: str | None = None
    examples: list[str] = field(default_factory=list)
    scenarios: list[str] = field(default_factory=list)
    event_type: str = field(default="case.created")

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        base = super().to_dict()
        base.update(
            {
                "raw_input": self.raw_input,
                "user_id": self.user_id,
                "examples": self.examples,
                "scenarios": self.scenarios,
            }
        )
        return base


@dataclass
class CaseCategorizedEvent(BaseEvent):
    """Event emitted when a case is categorized (receptionist files case)."""

    category: str = ""
    priority: str = "medium"
    confidence: float = 0.0
    structured_data: dict[str, Any] = field(default_factory=dict)
    labels: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    event_type: str = field(default="case.categorized")

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        base = super().to_dict()
        base.update(
            {
                "category": self.category,
                "priority": self.priority,
                "confidence": self.confidence,
                "structured_data": self.structured_data,
                "labels": self.labels,
                "keywords": self.keywords,
            }
        )
        return base


@dataclass
class CaseReferenceGeneratedEvent(BaseEvent):
    """Event emitted when reference file is generated."""

    reference_file_path: str = ""
    recommended_roles: list[str] = field(default_factory=list)
    recommended_tasks: list[str] = field(default_factory=list)
    workflow: list[str] = field(default_factory=list)
    event_type: str = field(default="case.reference_generated")

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        base = super().to_dict()
        base.update(
            {
                "reference_file_path": self.reference_file_path,
                "recommended_roles": self.recommended_roles,
                "recommended_tasks": self.recommended_tasks,
                "workflow": self.workflow,
            }
        )
        return base


@dataclass
class CaseExecutedEvent(BaseEvent):
    """Event emitted when agent starts executing a case."""

    agent_role: str = ""
    task: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    event_type: str = field(default="case.executed")

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        base = super().to_dict()
        base.update(
            {
                "agent_role": self.agent_role,
                "task": self.task,
                "started_at": self.started_at,
            }
        )
        return base


@dataclass
class CaseCompletedEvent(BaseEvent):
    """Event emitted when a case is completed."""

    outcome: str = ""  # success, partial, failure
    solution: str = ""
    completed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    agent_experience: dict[str, Any] = field(default_factory=dict)
    execution_time_seconds: float | None = None
    event_type: str = field(default="case.completed")

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        base = super().to_dict()
        base.update(
            {
                "outcome": self.outcome,
                "solution": self.solution,
                "completed_at": self.completed_at,
                "agent_experience": self.agent_experience,
                "execution_time_seconds": self.execution_time_seconds,
            }
        )
        return base
