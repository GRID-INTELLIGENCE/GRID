"""Pydantic models and type definitions for Canvas routing system."""

from __future__ import annotations

import builtins
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class RouteComplexity(str, Enum):
    """Complexity level of a route."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class SimilarityMatch:
    """Similarity match result."""

    path: Path
    similarity: float
    metadata: dict[str, Any]


@dataclass
class ScoredRoute:
    """Route with scoring information."""

    path: Path
    similarity: float
    complexity_penalty: float
    context_boost: float
    final_score: float
    metadata: builtins.dict[str, Any]

    def dict(self) -> builtins.dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": str(self.path),
            "similarity": self.similarity,
            "complexity_penalty": self.complexity_penalty,
            "context_boost": self.context_boost,
            "final_score": self.final_score,
            "metadata": self.metadata,
        }


class RouteResult:
    """Result of routing query."""

    def __init__(
        self,
        query: str,
        routes: list[ScoredRoute],
        confidence: float,
        total_candidates: int,
    ):
        self.query = query
        self.routes = routes
        self.confidence = confidence
        self.total_candidates = total_candidates


class RelevanceMetrics(BaseModel):
    """Individual relevance metrics."""

    semantic_similarity: float = Field(ge=0.0, le=1.0)
    path_complexity: float = Field(ge=0.0, le=1.0)
    context_match: float = Field(ge=0.0, le=1.0)
    usage_frequency: float = Field(ge=0.0, le=1.0)
    integration_alignment: float = Field(ge=0.0, le=1.0)


class RelevanceScore(BaseModel):
    """Relevance score with breakdown."""

    final_score: float = Field(ge=0.0, le=1.0)
    metrics: RelevanceMetrics
    confidence: float = Field(ge=0.0, le=1.0)

    def dict(self) -> builtins.dict[str, Any]:
        """Convert to dictionary."""
        return {
            "final_score": self.final_score,
            "metrics": self.metrics.model_dump(),
            "confidence": self.confidence,
        }


class TransferResult(BaseModel):
    """Result of state transfer."""

    success: bool
    coherence_level: float = Field(ge=0.0, le=1.0)
    transfer_signature: str
    integrity_check: str


class SensoryResult(BaseModel):
    """Result of sensory processing."""

    features: dict[str, Any]
    coherence: float = Field(ge=0.0, le=1.0)
    modality: str
    processed: dict[str, Any]


class MotivatedRoute(BaseModel):
    """Route with motivational adaptation."""

    route: ScoredRoute
    path_option: dict[str, Any] | None = None
    envelope_amplitude: float = Field(ge=0.0, le=1.0)
    motivation_score: float = Field(ge=0.0, le=1.0)


class MotivatedRouting(BaseModel):
    """Motivational routing result."""

    routes: list[MotivatedRoute]
    envelope_metrics: builtins.dict[str, Any] | None = None
    path_triage: builtins.dict[str, Any] | None = None
    urgency: float = Field(ge=0.0, le=1.0)

    def dict(self) -> builtins.dict[str, Any]:
        """Convert to dictionary."""
        return {
            "routes": [r.model_dump() if hasattr(r, "dict") else str(r) for r in self.routes],
            "envelope_metrics": self.envelope_metrics,
            "path_triage": self.path_triage,
            "urgency": self.urgency,
        }


class IntegrationStateUpdate(BaseModel):
    """Integration state update result."""

    success: bool
    previous_state: dict[str, Any]
    new_state: dict[str, Any]
    route_path: str | None = None


class CanvasRoutingResult(BaseModel):
    """Comprehensive canvas routing result."""

    query: str
    routes: list[ScoredRoute]
    relevance_scores: list[RelevanceScore]
    motivated_routing: MotivatedRouting | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    integration_alignment: float = Field(ge=0.0, le=1.0)
