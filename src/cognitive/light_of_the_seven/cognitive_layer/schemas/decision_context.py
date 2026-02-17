"""Decision context schema for decision-making support."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DecisionType(StrEnum):
    """Types of decisions."""

    ROUTINE = "routine"  # Familiar, low-stakes
    STRATEGIC = "strategic"  # High-stakes, complex
    TACTICAL = "tactical"  # Medium complexity
    EXPLORATORY = "exploratory"  # Novel, uncertain


class DecisionUrgency(StrEnum):
    """Urgency levels for decisions."""

    LOW = "low"  # Can take time
    MEDIUM = "medium"  # Moderate time pressure
    HIGH = "high"  # Urgent
    CRITICAL = "critical"  # Immediate


class DecisionContext(BaseModel):
    """Context for a decision-making situation."""

    # Decision identification
    decision_id: str = Field(description="Unique identifier for this decision")
    decision_type: DecisionType = Field(
        default=DecisionType.ROUTINE,
        description="Type of decision being made",
    )
    description: str = Field(
        default="",
        description="Human-readable description of the decision",
    )

    # Options and criteria
    options: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Available decision options",
    )
    criteria: list[dict[str, str]] = Field(
        default_factory=list,
        description="Decision criteria with weights",
    )

    # Context factors
    urgency: DecisionUrgency = Field(
        default=DecisionUrgency.LOW,
        description="Urgency level of the decision",
    )
    complexity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Complexity of the decision (0-1)",
    )
    familiarity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How familiar this decision type is (0-1)",
    )
    stakes: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Stakes of the decision (0-1)",
    )

    # Constraints
    time_constraint: float | None = Field(
        default=None,
        description="Time available for decision (seconds)",
    )
    information_available: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Amount of information available (0-1)",
    )

    # Bounded rationality parameters
    satisficing_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Threshold for satisficing (accept 'good enough')",
    )
    max_search_depth: int | None = Field(
        default=None,
        description="Maximum search depth for exploration",
    )

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    model_config = ConfigDict(use_enum_values=True)
