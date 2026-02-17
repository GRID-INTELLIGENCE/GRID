"""Prompt models for custom user prompts."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class PromptSource(StrEnum):
    """Source of prompt."""

    USER_CUSTOM = "user_custom"  # Highest priority - user's custom prompts
    ORG_DEFAULT = "org_default"
    SYSTEM_DEFAULT = "system_default"
    TEMPLATE = "template"
    DERIVED = "derived"


class PromptPriority(StrEnum):
    """Prompt priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PromptContext(BaseModel):
    """Context for prompt application."""

    user_id: str | None = Field(default=None, description="User context")
    org_id: str | None = Field(default=None, description="Organization context")
    session_id: str | None = Field(default=None, description="Session context")
    operation_type: str | None = Field(default=None, description="Operation type")
    domain: str | None = Field(default=None, description="Domain context")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class Prompt(BaseModel):
    """Prompt model."""

    prompt_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique prompt identifier")
    name: str = Field(description="Prompt name")
    content: str = Field(description="Prompt content")
    description: str | None = Field(default=None, description="Prompt description")

    # Source and priority
    source: PromptSource = Field(default=PromptSource.USER_CUSTOM, description="Prompt source")
    priority: PromptPriority = Field(default=PromptPriority.MEDIUM, description="Prompt priority")

    # Context matching
    context: PromptContext = Field(default_factory=PromptContext, description="Context for prompt")

    # Usage
    user_id: str | None = Field(default=None, description="User who owns/uses this prompt")
    org_id: str | None = Field(default=None, description="Organization context")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")

    # Template support
    is_template: bool = Field(default=False, description="Whether this is a template")
    template_variables: list[str] = Field(default_factory=list, description="Template variable names")
    template_defaults: dict[str, str] = Field(default_factory=dict, description="Template default values")

    # Usage tracking
    usage_count: int = Field(default=0, description="Number of times prompt was used")
    last_used: datetime | None = Field(default=None, description="Last usage timestamp")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Success rate (0-1)")

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(use_enum_values=True)

    @field_serializer("created_at", "updated_at", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO format."""
        return value.isoformat()

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(UTC)

    def render(self, variables: dict[str, str] | None = None) -> str:
        """Render template with variables.

        Args:
            variables: Variable values to substitute

        Returns:
            Rendered prompt content
        """
        if not self.is_template:
            return self.content

        rendered = self.content
        vars_to_use = {**self.template_defaults, **(variables or {})}

        for var_name in self.template_variables:
            placeholder = f"{{{var_name}}}"
            value = vars_to_use.get(var_name, "")
            rendered = rendered.replace(placeholder, value)

        return rendered

    def record_usage(self, success: bool = True) -> None:
        """Record prompt usage."""
        self.usage_count += 1
        self.last_used = datetime.now(UTC)

        # Update success rate (exponential moving average)
        alpha = 0.1
        if success:
            self.success_rate = alpha * 1.0 + (1 - alpha) * self.success_rate
        else:
            self.success_rate = alpha * 0.0 + (1 - alpha) * self.success_rate

        self.update_timestamp()
