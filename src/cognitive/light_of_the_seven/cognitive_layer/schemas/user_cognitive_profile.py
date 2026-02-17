"""User cognitive profile schema for personalization."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExpertiseLevel(str, Enum):
    """User expertise levels."""

    NOVICE = "novice"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LearningStyle(str, Enum):
    """Preferred learning styles."""

    ANALOGIES = "analogies"
    CODE_EXAMPLES = "code_examples"
    THEORY = "theory"
    VISUAL_DIAGRAMS = "visual_diagrams"
    HANDS_ON = "hands_on"


class DecisionStyle(str, Enum):
    """User decision-making styles."""

    QUICK = "quick"  # Prefer fast decisions
    DELIBERATE = "deliberate"  # Prefer thorough analysis
    BALANCED = "balanced"  # Adapt to context
    RISK_AVERSE = "risk_averse"  # Prefer safe options
    RISK_TAKING = "risk_taking"  # Prefer bold options


class UserCognitiveProfile(BaseModel):
    """Profile of user's cognitive characteristics and preferences."""

    # User identification
    user_id: str = Field(description="Unique user identifier")
    username: str | None = Field(default=None, description="User's name or handle")

    # Expertise
    expertise_level: ExpertiseLevel = Field(
        default=ExpertiseLevel.INTERMEDIATE,
        description="User's expertise level with the system",
    )
    domain_expertise: dict[str, ExpertiseLevel] = Field(
        default_factory=dict,
        description="Expertise levels in specific domains",
    )

    # Learning preferences
    learning_style: LearningStyle = Field(
        default=LearningStyle.CODE_EXAMPLES,
        description="Preferred learning style",
    )
    preferred_complexity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Preferred information complexity (0-1)",
    )

    # Decision-making preferences
    decision_style: DecisionStyle = Field(
        default=DecisionStyle.BALANCED,
        description="User's decision-making style",
    )
    satisficing_tendency: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Tendency to satisfice vs optimize (0-1)",
    )
    risk_tolerance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Risk tolerance level (0-1)",
    )

    # Cognitive capacity
    working_memory_capacity: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Estimated working memory capacity (0-1)",
    )
    cognitive_load_tolerance: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Tolerance for cognitive load (0-1)",
    )

    # Mental model
    mental_model_version: int = Field(
        default=1,
        description="Version of user's mental model",
    )
    model_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in mental model accuracy",
    )

    # Behavioral patterns
    interaction_history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="History of user interactions",
    )
    decision_patterns: dict[str, Any] = Field(
        default_factory=dict,
        description="Learned decision patterns",
    )

    # Preferences
    preferences: dict[str, Any] = Field(
        default_factory=dict,
        description="User preferences and settings",
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    model_config = ConfigDict(use_enum_values=True)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)
