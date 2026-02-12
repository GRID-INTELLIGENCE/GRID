"""
Pydantic Schema Definitions for Mistral AI Studio Agent Configuration

This module defines the data models for configuring Mistral AI Integration
Agents with ambiance settings including lighting, weather, sound, and seating.
"""

import os
from enum import Enum
from typing import Dict, Literal, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class LightingType(str, Enum):
    """Supported lighting types."""

    WARM = "warm"
    COOL = "cool"
    NEUTRAL = "neutral"


class LightingIntensity(str, Enum):
    """Supported lighting intensity levels."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class WeatherCondition(str, Enum):
    """Supported weather conditions."""

    RAIN = "rain"
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    STORM = "storm"


class WeatherIntensity(str, Enum):
    """Supported weather intensity levels."""

    LIGHT = "light"
    MODERATE = "moderate"
    MOODY = "moody"
    HEAVY = "heavy"


class AccelerationPattern(str, Enum):
    """Supported acceleration patterns for weather effects."""

    BREATHING = "breathing"
    STEADY = "steady"
    PULSING = "pulsing"
    RANDOM = "random"


class Genre(str, Enum):
    """Supported music genres."""

    JAZZ_AND_BLUES = "jazz_and_blues"
    CLASSICAL = "classical"
    AMBIENT = "ambient"
    ELECTRONIC = "electronic"
    ACOUSTIC = "acoustic"


class AmbientSoundIntensity(str, Enum):
    """Supported ambient sound intensity levels."""

    LOW = "low"
    MODERATE = "moderate"
    MODERATELY_BUSY = "moderately_busy"
    BUSY = "busy"


class LightingConfig(BaseModel):
    """Lighting configuration settings."""

    type: LightingType = Field(..., description="Type of lighting (warm/cool/neutral)")
    intensity: LightingIntensity = Field(..., description="Lighting intensity level")
    color_temperature: int = Field(
        ..., ge=2000, le=6500, description="Color temperature in Kelvin (2000-6500K)"
    )

    @field_validator("color_temperature")
    @classmethod
    def validate_color_temperature(cls, v: int) -> int:
        """Validate color temperature is within reasonable range."""
        if not 2000 <= v <= 6500:
            raise ValueError("Color temperature must be between 2000K and 6500K")
        return v


class WeatherConfig(BaseModel):
    """Weather condition configuration."""

    condition: WeatherCondition = Field(..., description="Weather condition type")
    intensity: WeatherIntensity = Field(..., description="Weather intensity level")
    acceleration_pattern: AccelerationPattern = Field(
        ..., description="Pattern for weather effect acceleration"
    )


class BackgroundMusicConfig(BaseModel):
    """Background music configuration."""

    genre: Genre = Field(..., description="Music genre")
    playlist: str = Field(..., description="Playlist name or identifier")
    current_track: str = Field(..., description="Current track identifier or name")


class AmbientSoundsConfig(BaseModel):
    """Ambient sounds configuration."""

    rain: AmbientSoundIntensity = Field(..., description="Rain sound intensity")
    coffee_shop: AmbientSoundIntensity = Field(
        ..., description="Coffee shop ambient sound intensity"
    )


class SoundConfig(BaseModel):
    """Sound configuration combining background music and ambient sounds."""

    background_music: BackgroundMusicConfig = Field(
        ..., description="Background music settings"
    )
    ambient_sounds: AmbientSoundsConfig = Field(
        ..., description="Ambient sounds settings"
    )


class SeatingConfig(BaseModel):
    """Seating location configuration."""

    location: str = Field(..., description="Seating location (e.g., 'balcony/roadside')")
    reason: str = Field(
        ..., description="Reason for seating choice (e.g., 'small_indoor_space')"
    )


class AmbianceConfig(BaseModel):
    """Complete ambiance configuration."""

    lighting: LightingConfig = Field(..., description="Lighting settings")
    weather: WeatherConfig = Field(..., description="Weather settings")
    sound: SoundConfig = Field(..., description="Sound settings (music + ambient)")
    seating: SeatingConfig = Field(..., description="Seating configuration")


class ApiEndpointConfig(BaseModel):
    """API endpoint configuration."""

    chat: str = Field(..., description="Chat completions endpoint path")
    models: str = Field(..., description="Models endpoint path")


class AuthenticationConfig(BaseModel):
    """API authentication configuration."""

    type: Literal["api_key"] = Field(default="api_key", description="Authentication type")
    env_var: str = Field(..., description="Environment variable name for API key")

    @field_validator("env_var")
    @classmethod
    def validate_env_var(cls, v: str) -> str:
        """Validate environment variable name format."""
        if not v or not v.isupper():
            raise ValueError("Environment variable name must be uppercase")
        return v


class ApiConfiguration(BaseModel):
    """API configuration for Mistral AI."""

    base_url: str = Field(..., description="Base URL for the API")
    endpoints: ApiEndpointConfig = Field(..., description="API endpoint paths")
    authentication: AuthenticationConfig = Field(
        ..., description="Authentication configuration"
    )

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate URL format."""
        try:
            result = urlparse(v)
            if not result.scheme or not result.netloc:
                raise ValueError("Invalid URL format")
            if result.scheme not in ["http", "https"]:
                raise ValueError("URL must use http or https scheme")
        except Exception as e:
            raise ValueError(f"Invalid base_url format: {e}")
        return v


class ModelParameters(BaseModel):
    """Model parameters for Mistral AI models."""

    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature (0.0-2.0)"
    )
    max_tokens: int = Field(
        default=100, ge=1, description="Maximum number of tokens to generate"
    )
    top_p: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter"
    )
    frequency_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty (-2.0 to 2.0)",
    )
    presence_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Presence penalty (-2.0 to 2.0)",
    )

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is within range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """Validate max_tokens is positive."""
        if v < 1:
            raise ValueError("max_tokens must be at least 1")
        return v


class ModelConfig(BaseModel):
    """Configuration for a single Mistral AI model."""

    model_id: str = Field(..., description="Model identifier (e.g., 'codestral', 'pixtral')")
    parameters: ModelParameters = Field(..., description="Model parameters")


class MistralStudioAgentConfig(BaseModel):
    """Complete Mistral AI Studio Agent configuration."""

    studio_name: str = Field(..., description="Studio name")
    agent_name: str = Field(..., description="Agent name")
    description: str = Field(
        ..., description="Agent description including ambiance context"
    )
    ambiance: AmbianceConfig = Field(..., description="Ambiance configuration")
    api_configuration: ApiConfiguration = Field(..., description="API configuration")
    models: Dict[str, ModelConfig] = Field(
        ..., description="Dictionary of model configurations by model_id"
    )
    environment_variables: Dict[str, str] = Field(
        default_factory=dict, description="Environment variable mappings"
    )

    def get_api_key(self) -> Optional[str]:
        """Get API key from environment variable."""
        env_var = self.api_configuration.authentication.env_var
        return os.getenv(env_var)

    def model_dump_json(self, **kwargs) -> str:
        """Export configuration to JSON string."""
        import json

        return json.dumps(self.model_dump(**kwargs), indent=2)

    @classmethod
    def from_json_file(cls, file_path: str) -> "MistralStudioAgentConfig":
        """Load configuration from JSON file."""
        import json

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    def to_json_file(self, file_path: str) -> None:
        """Save configuration to JSON file."""
        import json

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2)


# GRID Ecosystem Agent Configuration Models


class MistralAgentType(str, Enum):
    """Supported Mistral agent types."""

    STUDIO_AGENT = "studio_agent"
    GRID_AGENT = "grid_agent"


class PurposeConfig(BaseModel):
    """Purpose configuration for GRID agent tasks."""

    pattern_recognition: str = Field(
        ..., description="Purpose description for pattern recognition"
    )
    data_validation: str = Field(..., description="Purpose description for data validation")
    decision_logging: str = Field(..., description="Purpose description for decision logging")
    artifact_generation: str = Field(
        ..., description="Purpose description for artifact generation"
    )
    capability_retrieval: str = Field(
        ..., description="Purpose description for capability retrieval"
    )

    @field_validator("*", mode="before")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that description fields are non-empty."""
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("Purpose description must be a non-empty string")
        return v.strip()


class CommunicationGuidelines(BaseModel):
    """Communication guidelines for the agent."""

    clarity_and_conciseness: str = Field(
        ..., description="Guideline for clarity and conciseness"
    )
    context_awareness: str = Field(..., description="Guideline for context awareness")
    user_centric_approach: str = Field(
        ..., description="Guideline for user-centric approach"
    )

    @field_validator("*", mode="before")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that guideline fields are non-empty."""
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("Communication guideline must be a non-empty string")
        return v.strip()


class TaskConstraints(BaseModel):
    """Constraints for a specific task type."""

    context_window: Optional[str] = Field(
        default=None, description="Context window constraint"
    )
    confidence_thresholds: Optional[str] = Field(
        default=None, description="Confidence threshold constraints"
    )


class TaskExecutionConfig(BaseModel):
    """Task execution configuration for a specific task type."""

    description: str = Field(..., description="Task execution description")
    constraints: Optional[TaskConstraints] = Field(
        default=None, description="Task constraints"
    )
    feedback: Optional[str] = Field(default=None, description="Feedback guidelines")
    traceability: Optional[str] = Field(default=None, description="Traceability requirements")
    validation: Optional[str] = Field(default=None, description="Validation requirements")
    warnings: Optional[str] = Field(default=None, description="Warning requirements")

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate that description is non-empty."""
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("Task execution description must be a non-empty string")
        return v.strip()


class UnavailableServicesConfig(BaseModel):
    """Configuration for handling unavailable services."""

    description: str = Field(..., description="Description of unavailable services handling")
    communication: str = Field(
        ..., description="Communication guidelines for unavailable services"
    )

    @field_validator("*", mode="before")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that fields are non-empty."""
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("Field must be a non-empty string")
        return v.strip()


class ConfidenceThresholdsConfig(BaseModel):
    """Configuration for confidence thresholds."""

    description: str = Field(..., description="Description of confidence threshold handling")
    recommendations: str = Field(
        ..., description="Recommendations for improving confidence levels"
    )

    @field_validator("*", mode="before")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that fields are non-empty."""
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("Field must be a non-empty string")
        return v.strip()


class ValidationIssuesConfig(BaseModel):
    """Configuration for handling validation issues."""

    description: str = Field(..., description="Description of validation issue handling")
    actionability: str = Field(
        ..., description="Actionability requirements for validation results"
    )

    @field_validator("*", mode="before")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that fields are non-empty."""
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("Field must be a non-empty string")
        return v.strip()


class ErrorHandlingConfig(BaseModel):
    """Error handling configuration."""

    unavailable_services: UnavailableServicesConfig = Field(
        ..., description="Configuration for unavailable services"
    )
    confidence_thresholds: ConfidenceThresholdsConfig = Field(
        ..., description="Configuration for confidence thresholds"
    )
    validation_issues: ValidationIssuesConfig = Field(
        ..., description="Configuration for validation issues"
    )


class OutputFormattingConfig(BaseModel):
    """Output formatting configuration."""

    consistency: str = Field(
        ...,
        description="Consistency requirements including timestamps, IDs, and metadata",
    )
    readability: str = Field(..., description="Readability requirements for outputs")
    provenance: str = Field(
        ...,
        description="Provenance information requirements including source lines/references",
    )

    @field_validator("*", mode="before")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that fields are non-empty."""
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("Output formatting field must be a non-empty string")
        return v.strip()


class ConstraintsAndComplianceConfig(BaseModel):
    """Constraints and compliance configuration."""

    adherence_to_schema: str = Field(
        ...,
        description="Requirements for adherence to schemas (e.g., OPEN_POLICY.md contract)",
    )
    constraints: str = Field(
        ...,
        description="Constraints such as maximum analysis window, entity confidence thresholds, and relationship depth",
    )
    compliance: str = Field(
        ...,
        description="Compliance requirements with GRID ecosystem policies and guidelines",
    )

    @field_validator("*", mode="before")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that fields are non-empty."""
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("Constraints and compliance field must be a non-empty string")
        return v.strip()


class UserInteractionConfig(BaseModel):
    """User interaction configuration."""

    feedback: str = Field(..., description="Feedback guidelines for user inputs")
    transparency: str = Field(
        ..., description="Transparency requirements about capabilities and limitations"
    )
    responsiveness: str = Field(
        ..., description="Responsiveness requirements for user queries and requests"
    )

    @field_validator("*", mode="before")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that fields are non-empty."""
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("User interaction field must be a non-empty string")
        return v.strip()


class TaskExample(BaseModel):
    """Example for a specific task type."""

    description: str = Field(..., description="Description of the task example")
    example: str = Field(..., description="Example text or scenario")

    @field_validator("*", mode="before")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that fields are non-empty."""
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("Task example field must be a non-empty string")
        return v.strip()


class ExamplesConfig(BaseModel):
    """Examples configuration for all task types."""

    pattern_recognition: TaskExample = Field(
        ..., description="Pattern recognition example"
    )
    data_validation: TaskExample = Field(..., description="Data validation example")
    decision_logging: TaskExample = Field(..., description="Decision logging example")
    artifact_generation: TaskExample = Field(
        ..., description="Artifact generation example"
    )
    capability_retrieval: TaskExample = Field(
        ..., description="Capability retrieval example"
    )


class LimiterPluginConfig(BaseModel):
    """Limiter plugin configuration."""

    word_counter: str = Field(
        ..., description="Description of word counter functionality"
    )
    summarizer: str = Field(
        ..., description="Description of summarizer functionality"
    )
    warning_message_generator: str = Field(
        ..., description="Description of warning message generator functionality"
    )

    @field_validator("*", mode="before")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that fields are non-empty."""
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("Limiter plugin field must be a non-empty string")
        return v.strip()


class SystemPromptConfig(BaseModel):
    """System prompt configuration."""

    original_system_prompt: str = Field(..., description="Original system prompt text")
    summarized_system_prompt: str = Field(
        ..., description="Summarized system prompt text"
    )
    warning_message: str = Field(
        ..., description="Warning message for summarization"
    )

    @field_validator("*", mode="before")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that fields are non-empty."""
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("System prompt field must be a non-empty string")
        return v.strip()


class GridMistralAgentConfig(BaseModel):
    """Complete GRID ecosystem MistralAgent configuration."""

    agent_name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    purpose: PurposeConfig = Field(..., description="Purpose configuration")
    communication_guidelines: CommunicationGuidelines = Field(
        ..., description="Communication guidelines"
    )
    task_execution: Dict[str, TaskExecutionConfig] = Field(
        ...,
        description="Task execution configuration for each task type",
    )
    error_handling: ErrorHandlingConfig = Field(..., description="Error handling configuration")
    output_formatting: OutputFormattingConfig = Field(
        ..., description="Output formatting configuration"
    )
    constraints_and_compliance: ConstraintsAndComplianceConfig = Field(
        ..., description="Constraints and compliance configuration"
    )
    user_interaction: UserInteractionConfig = Field(
        ..., description="User interaction configuration"
    )
    examples: ExamplesConfig = Field(..., description="Examples configuration")
    limiter_plugin: LimiterPluginConfig = Field(
        ..., description="Limiter plugin configuration"
    )
    system_prompt_summarization: SystemPromptConfig = Field(
        ..., description="System prompt summarization configuration"
    )

    @field_validator("agent_name", "description", mode="before")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that agent name and description are non-empty."""
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("Agent name and description must be non-empty strings")
        return v.strip()

    @classmethod
    def from_json_file(cls, file_path: str) -> "GridMistralAgentConfig":
        """Load configuration from JSON file."""
        import json

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    def to_json_file(self, file_path: str) -> None:
        """Save configuration to JSON file."""
        import json

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2)


class ExtendedMistralStudioAgentConfig(BaseModel):
    """Extended configuration supporting both studio ambiance and GRID agent configurations."""

    agent_type: MistralAgentType = Field(
        ..., description="Type of agent configuration"
    )
    studio_agent_config: Optional[MistralStudioAgentConfig] = Field(
        default=None, description="Studio agent configuration (ambiance/API)"
    )
    grid_agent_config: Optional[GridMistralAgentConfig] = Field(
        default=None, description="GRID agent configuration (behavioral guidelines)"
    )

    @field_validator("agent_type")
    @classmethod
    def validate_agent_type(cls, v: MistralAgentType, info) -> MistralAgentType:
        """Validate that appropriate config is provided based on agent type."""
        # Note: This is a placeholder - actual validation would need to check the values
        return v

    @classmethod
    def from_json_file(cls, file_path: str) -> "ExtendedMistralStudioAgentConfig":
        """Load configuration from JSON file."""
        import json

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    def to_json_file(self, file_path: str) -> None:
        """Save configuration to JSON file."""
        import json

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2)
