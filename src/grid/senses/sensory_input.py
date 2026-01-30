"""Sensory input models."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class SensoryType(str, Enum):
    """Types of sensory inputs."""

    # Traditional senses
    VISUAL = "visual"
    AUDIO = "audio"
    TEXT = "text"

    # Extended cognitive senses
    SMELL = "smell"
    TOUCH = "touch"
    TASTE = "taste"

    # Abstract senses
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    VIBRATION = "vibration"
    PROXIMITY = "proximity"


class SensoryInput(BaseModel):
    """Sensory input data."""

    input_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique input identifier")
    sensory_type: SensoryType = Field(description="Type of sensory input")
    data: dict[str, Any] = Field(description="Sensory data")
    intensity: float = Field(default=1.0, ge=0.0, le=1.0, description="Intensity (0-1)")
    quality: str | None = Field(default=None, description="Quality descriptor")
    source: str | None = Field(default=None, description="Source of input")
    location: dict[str, float] | None = Field(default=None, description="Spatial location")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(use_enum_values=True, json_encoders={datetime: lambda v: v.isoformat()})

    # Type-specific data accessors
    def get_visual_data(self) -> dict[str, Any] | None:
        """Get visual data if available."""
        if self.sensory_type == SensoryType.VISUAL:
            return self.data
        return None

    def get_audio_data(self) -> dict[str, Any] | None:
        """Get audio data if available."""
        if self.sensory_type == SensoryType.AUDIO:
            return self.data
        return None

    def get_smell_data(self) -> dict[str, Any] | None:
        """Get smell data if available."""
        if self.sensory_type == SensoryType.SMELL:
            return {
                "scent": self.data.get("scent", "unknown"),
                "intensity": self.intensity,
                "quality": self.quality,
            }
        return None

    def get_touch_data(self) -> dict[str, Any] | None:
        """Get touch data if available."""
        if self.sensory_type == SensoryType.TOUCH:
            return {
                "texture": self.data.get("texture", "unknown"),
                "temperature": self.data.get("temperature", 0.0),
                "pressure": self.data.get("pressure", 0.0),
                "intensity": self.intensity,
            }
        return None

    def get_taste_data(self) -> dict[str, Any] | None:
        """Get taste data if available."""
        if self.sensory_type == SensoryType.TASTE:
            return {
                "flavor": self.data.get("flavor", "unknown"),
                "intensity": self.intensity,
                "quality": self.quality,
            }
        return None
