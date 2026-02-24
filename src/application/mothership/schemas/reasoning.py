"""
Reasoning stabilization schemas.

Pydantic schemas for reasoning stabilization, drift detection, and
roundtable reconciliation endpoints.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class RiskLevel(StrEnum):
    """Risk level for reasoning operations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GapSource(StrEnum):
    """Source that generated an inference gap."""

    STABILIZE = "stabilize"
    DRIFT_CHECK = "drift_check"
    ROUNDTABLE_RECONCILE = "roundtable_reconcile"


class GapStatus(StrEnum):
    """Lifecycle state for an inference gap."""

    OPEN = "open"
    RESOLVED = "resolved"


class ReasoningTrace(BaseModel):
    """Single structured reasoning step."""

    step_number: int = Field(..., ge=1)
    stage: str = Field(..., min_length=1, max_length=120)
    statement: str = Field(..., min_length=1, max_length=4000)
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UncertaintySpan(BaseModel):
    """Region in text where uncertainty or assumptions were detected."""

    text: str = Field(..., min_length=1, max_length=400)
    reason: str = Field(..., min_length=1, max_length=400)
    severity: Literal["low", "medium", "high"] = Field(default="medium")
    start_index: int | None = Field(default=None, ge=0)
    end_index: int | None = Field(default=None, ge=0)


class DriftSignal(BaseModel):
    """Signal indicating response drift or coherence risk."""

    signal_type: Literal["intent_shift", "contradiction", "unsupported_claim", "coherence_drop"]
    severity: Literal["low", "medium", "high"]
    message: str = Field(..., min_length=1, max_length=500)
    evidence: list[str] = Field(default_factory=list)


class DecisionQualityRecord(BaseModel):
    """Quality metrics for stabilized reasoning output."""

    quality_score: float = Field(..., ge=0.0, le=1.0)
    coherence: float = Field(..., ge=0.0, le=1.0)
    evidence_coverage: float = Field(..., ge=0.0, le=1.0)
    uncertainty_penalty: float = Field(..., ge=0.0, le=1.0)
    recommendations: list[str] = Field(default_factory=list)
    measured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class InferenceGapRecord(BaseModel):
    """Persistent record of unresolved reasoning gap."""

    gap_id: str = Field(..., min_length=1, max_length=64)
    case_id: str = Field(..., min_length=1, max_length=120)
    source: GapSource
    summary: str = Field(..., min_length=1, max_length=1200)
    status: GapStatus = GapStatus.OPEN
    confidence: float = Field(..., ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StabilizeRequest(BaseModel):
    """Request payload for reasoning stabilization."""

    input: str = Field(..., min_length=1, max_length=50000)
    context: dict[str, Any] = Field(default_factory=dict)
    task_type: str = Field(default="general", min_length=1, max_length=120)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    case_id: str | None = Field(default=None, max_length=120)
    include_gap_log: bool = True


class StabilizeResponse(BaseModel):
    """Response payload for reasoning stabilization."""

    stabilized_trace: list[ReasoningTrace]
    uncertainty_map: list[UncertaintySpan]
    next_actions: list[str]
    quality_record: DecisionQualityRecord
    logged_gaps: list[InferenceGapRecord] = Field(default_factory=list)


class DriftCheckRequest(BaseModel):
    """Request payload for response drift checks."""

    trace_so_far: list[dict[str, Any] | str] | str = Field(default_factory=list)
    candidate_response: str = Field(..., min_length=1, max_length=50000)
    case_id: str | None = Field(default=None, max_length=120)
    include_gap_log: bool = True


class DriftCheckResponse(BaseModel):
    """Response payload for drift checks."""

    drift_flags: list[DriftSignal]
    contradictions: list[str]
    repair_suggestions: list[str]
    logged_gaps: list[InferenceGapRecord] = Field(default_factory=list)


class RoundtableReconcileRequest(BaseModel):
    """Request payload for human/system reconciliation."""

    case_id: str = Field(..., min_length=1, max_length=120)
    human_notes: list[str] | str
    system_trace: list[dict[str, Any] | str] | str
    topic: str | None = Field(default=None, max_length=250)


class RoundtableReconcileResponse(BaseModel):
    """Response payload for reconciliation output."""

    resolved_facts: list[str]
    open_gaps: list[InferenceGapRecord]
    updated_policy_hints: list[str]
    synthesis: str


class InferenceGapListResponse(BaseModel):
    """Response payload for listing inference gaps by case."""

    case_id: str
    total: int
    records: list[InferenceGapRecord]
