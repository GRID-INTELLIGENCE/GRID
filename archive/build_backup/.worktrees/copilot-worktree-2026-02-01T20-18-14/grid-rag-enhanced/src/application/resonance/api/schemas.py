"""
Activity Resonance API Request/Response Schemas.

Pydantic models for validating incoming API requests and responses
with comprehensive field validation and documentation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Base Configuration
# =============================================================================


class BaseRequest(BaseModel):
    """Base request model with common configuration."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        populate_by_name=True,
    )


class BaseResponse(BaseModel):
    """Base response model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )


# =============================================================================
# Enums
# =============================================================================


class ActivityType(str, Enum):
    """Types of activities."""

    GENERAL = "general"
    CODE = "code"
    CONFIG = "config"


class ContextType(str, Enum):
    """Types of context."""

    GENERAL = "general"
    CODE = "code"
    CONFIG = "config"


# =============================================================================
# Request Models
# =============================================================================


class ActivityProcessRequest(BaseRequest):
    """Request to process an activity with left-to-right communication."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The query or goal to process",
        examples=["create a new service"],
    )
    activity_type: ActivityType = Field(
        default=ActivityType.GENERAL,
        description="Type of activity",
    )
    context: dict[str, Any] | None = Field(
        default_factory=dict,
        description="Additional context for processing",
    )


class ContextQueryRequest(BaseRequest):
    """Request to get fast context for a query."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The query to get context for",
    )
    context_type: ContextType = Field(
        default=ContextType.GENERAL,
        description="Type of context needed",
    )
    max_length: int = Field(
        default=200,
        ge=50,
        le=2000,
        description="Maximum context length in characters",
    )


class PathTriageRequest(BaseRequest):
    """Request to get path triage for a goal."""

    goal: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The goal or task",
        examples=["implement authentication"],
    )
    context: dict[str, Any] | None = Field(
        default_factory=dict,
        description="Optional context for path generation",
    )
    max_options: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of path options to generate",
    )


class DefinitiveStepRequest(BaseRequest):
    """Request to run the 'definitive' (canvas-flip) step."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "query": "Where do these features connect and what is the main function of this update?",
                    "activity_type": "general",
                    "context": {},
                    "progress": 0.65,
                    "target_schema": "context_engineering",
                    "use_rag": False,
                    "use_llm": False,
                    "max_chars": 200,
                }
            ]
        },
    )

    query: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="The query, goal, or freeform narrative to align",
    )
    activity_type: ActivityType = Field(
        default=ActivityType.GENERAL,
        description="Type of activity",
    )
    context: dict[str, Any] | None = Field(
        default_factory=dict,
        description="Optional context for processing",
    )
    progress: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Progress ratio hint (0..1). 0.65 represents the 'red light' checkpoint",
    )
    target_schema: str = Field(
        default="context_engineering",
        min_length=1,
        max_length=128,
        description="Schema name for transform.schema_map (e.g., context_engineering, resonance, knowledgebase)",
    )
    use_rag: bool = Field(
        default=False,
        description="If true, enrich the response with a local-first RAG query (requires an existing index)",
    )
    use_llm: bool = Field(
        default=False,
        description="If true, allow LLM-backed behavior (local Ollama only). Heuristic-only by default.",
    )
    max_chars: int = Field(
        default=280,
        ge=20,
        le=2000,
        description="Character budget for the compressed 'one-line' summary",
    )


# =============================================================================
# Response Models - Context
# =============================================================================


class ContextMetricsResponse(BaseResponse):
    """Context quality and decision tension metrics."""

    sparsity: float = Field(..., ge=0.0, le=1.0, description="Context sparsity (0.0=dense, 1.0=sparse)")
    attention_tension: float = Field(..., ge=0.0, le=1.0, description="Attention tension (0.0=relaxed, 1.0=tense)")
    decision_pressure: float = Field(..., ge=0.0, le=1.0, description="Decision pressure (0.0=low, 1.0=high)")
    clarity: float = Field(..., ge=0.0, le=1.0, description="Query clarity (0.0=unclear, 1.0=clear)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="System confidence (0.0=uncertain, 1.0=confident)")


class ContextResponse(BaseResponse):
    """Response with context snapshot."""

    content: str = Field(..., description="Context content")
    source: str = Field(..., description="Context source")
    metrics: ContextMetricsResponse = Field(..., description="Context metrics")
    timestamp: float = Field(..., description="Timestamp when context was generated")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")


# =============================================================================
# Response Models - Paths
# =============================================================================


class PathOptionResponse(BaseResponse):
    """A single path option."""

    id: str = Field(..., description="Path option ID")
    name: str = Field(..., description="Path name")
    description: str = Field(..., description="Path description")
    complexity: str = Field(..., description="Complexity level")
    steps: list[str] = Field(..., description="Step-by-step breakdown")
    input_scenario: str = Field(..., description="Input scenario")
    output_scenario: str = Field(..., description="Output scenario")
    estimated_time: float = Field(..., ge=0.0, description="Estimated time in seconds")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    recommendation_score: float = Field(..., ge=0.0, le=1.0, description="Recommendation score")


class PathTriageResponse(BaseResponse):
    """Response with path triage options."""

    goal: str = Field(..., description="The goal or task")
    options: list[PathOptionResponse] = Field(..., description="Path options")
    recommended: PathOptionResponse | None = Field(None, description="Recommended path option")
    glimpse_summary: str = Field(..., description="Quick glimpse summary")
    total_options: int = Field(..., ge=0, description="Total number of options")


# =============================================================================
# Response Models - Envelope
# =============================================================================


class EnvelopeMetricsResponse(BaseResponse):
    """ADSR envelope metrics."""

    phase: str = Field(..., description="Current envelope phase")
    amplitude: float = Field(..., ge=0.0, le=1.0, description="Current amplitude")
    velocity: float = Field(..., description="Rate of change")
    time_in_phase: float = Field(..., ge=0.0, description="Time in current phase (seconds)")
    total_time: float = Field(..., ge=0.0, description="Total envelope time (seconds)")
    peak_amplitude: float = Field(..., ge=0.0, le=1.0, description="Peak amplitude reached")


# =============================================================================
# Response Models - Activity
# =============================================================================


class ResonanceResponse(BaseResponse):
    """Full resonance response with context, paths, and envelope."""

    activity_id: str = Field(..., description="Activity ID")
    state: str = Field(..., description="Current resonance state")
    urgency: float = Field(..., ge=0.0, le=1.0, description="Urgency level")
    message: str = Field(..., description="Status message")
    context: ContextResponse | None = Field(None, description="Context snapshot")
    paths: PathTriageResponse | None = Field(None, description="Path triage")
    envelope: EnvelopeMetricsResponse | None = Field(None, description="Envelope metrics")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ActivityCompleteResponse(BaseResponse):
    """Response for activity completion."""

    activity_id: str = Field(..., description="Activity ID")
    completed: bool = Field(..., description="Whether activity was completed")
    message: str = Field(..., description="Completion message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")


class ActivityEventResponse(BaseResponse):
    """A single activity event."""

    event_id: str = Field(..., description="Event ID")
    timestamp: float = Field(..., description="Event timestamp")
    activity_type: str = Field(..., description="Activity type")
    payload: dict[str, Any] = Field(..., description="Event payload")


class ActivityEventsResponse(BaseResponse):
    """Response with activity events history."""

    activity_id: str = Field(..., description="Activity ID")
    events: list[ActivityEventResponse] = Field(..., description="List of events")
    total: int = Field(..., ge=0, description="Total number of events")


class FAQItemResponse(BaseResponse):
    """FAQ item for audience-facing explanations."""

    question: str = Field(..., description="FAQ question")
    answer: str = Field(..., description="FAQ answer")


class UseCaseResponse(BaseResponse):
    """A short use-case scenario."""

    audience: str = Field(..., description="Audience segment")
    scenario: str = Field(..., description="Use-case scenario")
    entrypoint: str = Field(..., description="How to trigger (CLI or API)")
    output: str = Field(..., description="Expected output")


class DefinitiveChoiceResponse(BaseResponse):
    """A metaphor-labeled path option (left/right/straight)."""

    direction: str = Field(..., description="Metaphor direction: left | right | straight")
    option: PathOptionResponse = Field(..., description="Path option")
    why: str = Field(..., description="When to choose this path")


class DefinitiveStepResponse(BaseResponse):
    """Response for the 'definitive' (canvas-flip) step."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "activity_id": "550e8400-e29b-41d4-a716-446655440000",
                    "progress": 0.65,
                    "canvas_before": (
                        "Canvas inverted: free-form work looks chaotic because " "the viewing frame is flipped."
                    ),
                    "canvas_after": "Canvas flipped: context, options, and structured intent become visible.",
                    "summary": "At the ~65% checkpoint, Resonance aligns the view and produces structured output.",
                    "faq": [{"question": "What is this?", "answer": "A mid-process checkpoint."}],
                    "use_cases": [
                        {
                            "audience": "Builders",
                            "scenario": "Convert a vague goal into structured plan.",
                            "entrypoint": "POST /api/v1/resonance/definitive",
                            "output": "Structured schema + path choices",
                        }
                    ],
                    "api_mechanics": ["POST /api/v1/resonance/definitive"],
                    "structured": {},
                    "context": None,
                    "paths": None,
                    "choices": [],
                    "skills": {},
                    "rag": None,
                }
            ]
        },
    )

    activity_id: str = Field(..., description="Activity ID")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress ratio hint (0..1)")
    canvas_before: str = Field(..., description="Pre-checkpoint view state")
    canvas_after: str = Field(..., description="Post-checkpoint view state")
    summary: str = Field(..., description="One-line compressed explanation")
    faq: list[FAQItemResponse] = Field(default_factory=list, description="Audience-facing FAQ")
    use_cases: list[UseCaseResponse] = Field(default_factory=list, description="Use-case scenarios")
    api_mechanics: list[str] = Field(default_factory=list, description="Key entry points and mechanics")
    structured: dict[str, Any] = Field(default_factory=dict, description="Structured schema transform output")
    context: ContextResponse | None = Field(None, description="Context snapshot")
    paths: PathTriageResponse | None = Field(None, description="Path triage")
    choices: list[DefinitiveChoiceResponse] = Field(default_factory=list, description="Metaphor-labeled path choices")
    skills: dict[str, Any] = Field(default_factory=dict, description="Raw skill outputs (for debugging/inspection)")
    rag: dict[str, Any] | None = Field(None, description="Optional RAG enrichment payload")


# =============================================================================
# WebSocket Models
# =============================================================================


class WebSocketFeedbackMessage(BaseResponse):
    """WebSocket message with resonance feedback."""

    activity_id: str = Field(..., description="Activity ID")
    state: str = Field(..., description="Current state")
    urgency: float = Field(..., ge=0.0, le=1.0, description="Urgency level")
    message: str = Field(..., description="Feedback message")
    envelope: EnvelopeMetricsResponse | None = Field(None, description="Envelope metrics")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


# =============================================================================
# Error Response Models
# =============================================================================


class ErrorResponse(BaseResponse):
    """Error response model."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Error detail")
    activity_id: str | None = Field(None, description="Activity ID if applicable")


__all__ = [
    # Base
    "BaseRequest",
    "BaseResponse",
    # Enums
    "ActivityType",
    "ContextType",
    # Requests
    "ActivityProcessRequest",
    "ContextQueryRequest",
    "PathTriageRequest",
    "DefinitiveStepRequest",
    # Responses - Context
    "ContextMetricsResponse",
    "ContextResponse",
    # Responses - Paths
    "PathOptionResponse",
    "PathTriageResponse",
    # Responses - Envelope
    "EnvelopeMetricsResponse",
    # Responses - Activity
    "ResonanceResponse",
    "ActivityCompleteResponse",
    "ActivityEventResponse",
    "ActivityEventsResponse",
    "FAQItemResponse",
    "UseCaseResponse",
    "DefinitiveChoiceResponse",
    "DefinitiveStepResponse",
    # WebSocket
    "WebSocketFeedbackMessage",
    # Error
    "ErrorResponse",
]
