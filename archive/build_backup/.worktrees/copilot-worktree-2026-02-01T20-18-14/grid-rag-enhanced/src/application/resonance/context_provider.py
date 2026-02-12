"""
Fast Context Provider - Left Side (application/).

Provides fast, concise context when decision/attention metrics are tense.
Vividly explains when context is sparse.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ContextMetrics:
    """Metrics for context quality and decision tension."""

    sparsity: float = 0.0  # 0.0 = dense, 1.0 = sparse
    attention_tension: float = 0.0  # 0.0 = relaxed, 1.0 = tense
    decision_pressure: float = 0.0  # 0.0 = low, 1.0 = high
    clarity: float = 1.0  # 0.0 = unclear, 1.0 = clear
    confidence: float = 0.5  # 0.0 = uncertain, 1.0 = confident


@dataclass
class ContextSnapshot:
    """A snapshot of context at a moment in time."""

    content: str
    source: str
    metrics: ContextMetrics
    timestamp: float
    relevance_score: float = 0.5


class ContextProvider:
    """
    Fast, concise context provider from application/ directory.

    Provides vivid explanations when context is sparse and decision/attention
    metrics are tense. Optimized for speed and clarity.
    """

    def __init__(self, application_path: Path | None = None):
        """
        Initialize context provider.

        Args:
            application_path: Path to application directory
        """
        if application_path is None:
            # Default to workspace application directory
            application_path = Path(__file__).parent.parent
        self.application_path = Path(application_path)
        self._cache: dict[str, ContextSnapshot] = {}

    def assess_context_metrics(self, query: str, available_context: dict[str, Any] | None = None) -> ContextMetrics:
        """
        Assess context quality and decision tension metrics.

        Args:
            query: The query or task at hand
            available_context: Optional existing context

        Returns:
            Context metrics
        """
        # Assess sparsity (how much context is missing)
        sparsity = 0.5  # Default moderate sparsity
        if available_context:
            # More context = less sparsity
            context_keys = len(available_context)
            sparsity = max(0.0, 1.0 - (context_keys / 10.0))
        else:
            sparsity = 0.8  # High sparsity if no context

        # Assess attention tension (urgency, complexity)
        query_length = len(query.split())
        attention_tension = min(1.0, query_length / 50.0)  # Longer queries = more tension

        # Assess decision pressure (how many choices/options)
        decision_pressure = 0.3  # Default moderate
        if "?" in query or "choose" in query.lower() or "option" in query.lower():
            decision_pressure = 0.7  # Higher if choosing

        # Assess clarity (how clear the query is)
        clarity = 1.0
        if len(query) < 10:
            clarity = 0.5  # Very short queries are unclear
        if "?" not in query and len(query.split()) < 3:
            clarity = 0.6  # Ambiguous queries

        # Assess confidence (how confident we can be)
        confidence = 0.5
        if available_context and len(available_context) > 3:
            confidence = 0.8  # More context = more confidence
        if sparsity > 0.7:
            confidence = 0.3  # High sparsity = low confidence

        return ContextMetrics(
            sparsity=sparsity,
            attention_tension=attention_tension,
            decision_pressure=decision_pressure,
            clarity=clarity,
            confidence=confidence,
        )

    def provide_context(self, query: str, context_type: str = "general", max_length: int = 200) -> ContextSnapshot:
        """
        Provide fast, concise context for a query.

        Args:
            query: The query or task
            context_type: Type of context needed ("general", "code", "config")
            max_length: Maximum context length in characters

        Returns:
            Context snapshot with content and metrics
        """
        import time

        # Check cache
        cache_key = f"{context_type}:{query[:50]}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            # Return cached if recent (within 5 minutes)
            if time.time() - cached.timestamp < 300:
                return cached

        # Assess metrics
        metrics = self.assess_context_metrics(query)

        # Generate context based on type
        if context_type == "code":
            content = self._provide_code_context(query, max_length)
        elif context_type == "config":
            content = self._provide_config_context(query, max_length)
        else:
            content = self._provide_general_context(query, max_length)

        # Adjust content based on metrics
        if metrics.sparsity > 0.7:
            # High sparsity - add vivid explanation
            content = f"⚠️ Sparse context detected. {content} [Context gap: {metrics.sparsity:.1%}]"

        if metrics.attention_tension > 0.7:
            # High tension - emphasize urgency
            content = f"⚡ Tense attention metrics. {content} [Tension: {metrics.attention_tension:.1%}]"

        if metrics.decision_pressure > 0.7:
            # High decision pressure - provide decision support
            content = f"🎯 Decision pressure high. {content} [Pressure: {metrics.decision_pressure:.1%}]"

        snapshot = ContextSnapshot(
            content=content[:max_length],
            source=f"application/{context_type}",
            metrics=metrics,
            timestamp=time.time(),
            relevance_score=1.0 - metrics.sparsity,
        )

        # Cache result
        self._cache[cache_key] = snapshot
        return snapshot

    def _provide_general_context(self, query: str, max_length: int) -> str:
        """Provide general context."""
        # Fast, concise explanation
        query_lower = query.lower()
        if "error" in query_lower or "fail" in query_lower:
            return "Error context: Check logs, verify config, review recent changes."
        if "test" in query_lower:
            return "Test context: Run pytest, check coverage, verify fixtures."
        if "api" in query_lower or "endpoint" in query_lower:
            return "API context: FastAPI routes, middleware, request/response models."
        return f"Context: {query[:max_length-20]}"

    def _provide_code_context(self, query: str, max_length: int) -> str:
        """Provide code-specific context."""
        # Look for relevant files in application/
        query_lower = query.lower()
        if "service" in query_lower:
            return "Service context: Check services/ directory, dependency injection patterns."
        if "model" in query_lower or "schema" in query_lower:
            return "Model context: Pydantic models in models/ or schemas/, type validation."
        if "router" in query_lower or "route" in query_lower:
            return "Router context: FastAPI routers in routers/, endpoint definitions."
        return "Code context: Python 3.11+, type hints, Pydantic models, FastAPI."

    def _provide_config_context(self, query: str, max_length: int) -> str:
        """Provide configuration context."""
        config_path = self.application_path / "mothership" / "config.py"
        if config_path.exists():
            return "Config context: MothershipSettings, environment variables, validation."
        return "Config context: Check config.py, environment variables, settings classes."

    def clear_cache(self) -> None:
        """Clear context cache."""
        self._cache.clear()
