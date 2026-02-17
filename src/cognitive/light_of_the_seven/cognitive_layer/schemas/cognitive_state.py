"""Cognitive state schema for tracking user cognitive factors."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CognitiveLoadType(str, Enum):
    """Types of cognitive load."""

    INTRINSIC = "intrinsic"  # Inherent difficulty
    EXTRINSIC = "extrinsic"  # Poor design
    GERMANE = "germane"  # Schema construction


class ProcessingMode(str, Enum):
    """Dual-process theory modes."""

    SYSTEM_1 = "system_1"  # Fast, automatic, intuitive
    SYSTEM_2 = "system_2"  # Slow, deliberate, analytical


class CognitiveState(BaseModel):
    """Represents the current cognitive state of a user interaction."""

    # Cognitive load metrics
    estimated_load: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0,
        description="Estimated cognitive load (0-10 scale)",
    )
    load_type: CognitiveLoadType = Field(
        default=CognitiveLoadType.INTRINSIC,
        description="Primary type of cognitive load",
    )
    working_memory_usage: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Working memory usage (0-1, where 1 = capacity)",
    )

    # Processing mode
    processing_mode: ProcessingMode = Field(
        default=ProcessingMode.SYSTEM_1,
        description="Current processing mode (System 1 or System 2)",
    )
    mode_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in processing mode selection",
    )

    # Mental model alignment
    mental_model_alignment: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Alignment between user expectations and system behavior (0-1)",
    )
    model_mismatches: list[str] = Field(
        default_factory=list,
        description="List of detected mental model mismatches",
    )

    # Decision context
    decision_complexity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Complexity of current decision (0-1)",
    )
    time_pressure: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Time pressure level (0-1)",
    )

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context information",
    )

    model_config = ConfigDict(use_enum_values=True)
