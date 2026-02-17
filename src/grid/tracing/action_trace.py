"""Action trace models for source tracking."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class TraceOrigin(StrEnum):
    """Origin types for action traces."""

    USER_INPUT = "user_input"
    API_REQUEST = "api_request"
    SCHEDULED_TASK = "scheduled_task"
    EVENT_TRIGGER = "event_trigger"
    SYSTEM_INIT = "system_init"
    COGNITIVE_DECISION = "cognitive_decision"
    PATTERN_MATCH = "pattern_match"
    EXTERNAL_WEBHOOK = "external_webhook"
    INTERNAL_PIPELINE = "internal_pipeline"
    EMERGENCY_REALTIME = "emergency_realtime"
    # AI Safety origins
    MODEL_INFERENCE = "model_inference"
    SAFETY_ANALYSIS = "safety_analysis"
    COMPLIANCE_CHECK = "compliance_check"
    GUARDRAIL_VIOLATION = "guardrail_violation"
    RISK_ASSESSMENT = "risk_assessment"
    PROMPT_VALIDATION = "prompt_validation"
    PII_DETECTION = "pii_detection"


class TraceContext(BaseModel):
    """Context information for action tracing."""

    # Identification
    trace_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique trace identifier")
    parent_trace_id: str | None = Field(default=None, description="Parent trace ID for nested operations")
    root_trace_id: str | None = Field(default=None, description="Root trace ID for operation tree")

    # Origin tracking
    origin: TraceOrigin = Field(description="Origin type of the action")
    source_module: str = Field(description="Module where action originated")
    source_function: str = Field(description="Function where action originated")
    source_file: str | None = Field(default=None, description="Source file path")
    source_line: int | None = Field(default=None, description="Source line number")

    # User/Org context
    user_id: str | None = Field(default=None, description="User who initiated the action")
    org_id: str | None = Field(default=None, description="Organization context")
    session_id: str | None = Field(default=None, description="Session identifier")

    # Request context
    request_id: str | None = Field(default=None, description="HTTP request ID")
    operation_id: str | None = Field(default=None, description="Operation identifier")

    # Timing
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Action timestamp")
    duration_ms: float | None = Field(default=None, description="Action duration in milliseconds")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional trace metadata")
    tags: set[str] = Field(default_factory=set, description="Tags for categorization")

    model_config = ConfigDict(use_enum_values=True)

    @field_serializer("timestamp", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO format."""
        return value.isoformat()

    @field_serializer("tags", when_used="json")
    def serialize_set(self, value: set[str]) -> list:
        """Serialize set to list."""
        return list(value)


class ActionTrace(BaseModel):
    """Complete action trace with full provenance."""

    # Core identification
    trace_id: str = Field(description="Unique trace identifier")
    action_type: str = Field(description="Type of action performed")
    action_name: str = Field(description="Human-readable action name")

    # Context chain
    context: TraceContext = Field(description="Trace context")
    parent_traces: list[str] = Field(default_factory=list, description="Chain of parent trace IDs")
    child_traces: list[str] = Field(default_factory=list, description="Child trace IDs")

    # Action details
    input_data: dict[str, Any] = Field(default_factory=dict, description="Input data snapshot")
    output_data: dict[str, Any] | None = Field(default=None, description="Output data snapshot")
    intermediate_states: list[dict[str, Any]] = Field(default_factory=list, description="Intermediate state snapshots")

    # Results
    success: bool = Field(default=True, description="Whether action succeeded")
    error: str | None = Field(default=None, description="Error message if failed")
    error_traceback: str | None = Field(default=None, description="Full traceback if error occurred")

    # Impact tracking
    affected_resources: list[str] = Field(default_factory=list, description="Resources affected by this action")
    downstream_effects: list[str] = Field(default_factory=list, description="Downstream effects/actions triggered")

    # Cognitive context
    cognitive_state: dict[str, Any] | None = Field(default=None, description="Cognitive state at action time")
    decision_factors: list[dict[str, Any]] = Field(default_factory=list, description="Factors influencing decision")

    # Quantization
    quantized_steps: list[dict[str, Any]] = Field(default_factory=list, description="Quantized processing steps")
    quantization_level: int | None = Field(default=None, description="Quantization granularity level")

    # Sensory context
    sensory_inputs: dict[str, Any] = Field(
        default_factory=dict, description="Sensory inputs (visual, audio, smell, touch, taste)"
    )

    # Timing
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = Field(default=None)
    duration_ms: float | None = Field(default=None)

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    version: int = Field(default=1, description="Trace version")

    # AI Safety specific fields
    model_used: str | None = Field(default=None, description="AI model invoked")
    safety_score: float | None = Field(default=None, description="AI safety assessment score")
    prompt_hash: str | None = Field(default=None, description="Hash for prompt security tracking")
    guardrail_violations: list[str] = Field(default_factory=list, description="Safety rule breaches")
    risk_level: str | None = Field(default=None, description="Risk assessment: low/medium/high")
    compliance_flags: list[str] = Field(default_factory=list, description="Compliance issues detected")

    model_config = ConfigDict(use_enum_values=True)

    @field_serializer("created_at", "completed_at", when_used="json")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        """Serialize datetime to ISO format."""
        return value.isoformat() if value else None

    def complete(
        self, output_data: dict[str, Any] | None = None, success: bool = True, error: str | None = None
    ) -> None:
        """Mark trace as completed."""
        self.completed_at = datetime.now(UTC)
        if self.context.timestamp:
            delta = self.completed_at - self.context.timestamp
            self.duration_ms = delta.total_seconds() * 1000
        self.success = success
        if output_data:
            self.output_data = output_data
        if error:
            self.error = error

    def add_child_trace(self, child_trace_id: str) -> None:
        """Add a child trace ID."""
        if child_trace_id not in self.child_traces:
            self.child_traces.append(child_trace_id)

    def add_quantized_step(self, step: dict[str, Any]) -> None:
        """Add a quantized processing step."""
        self.quantized_steps.append(step)

    def add_sensory_input(self, sense_type: str, data: Any) -> None:
        """Add sensory input data."""
        self.sensory_inputs[sense_type] = data
