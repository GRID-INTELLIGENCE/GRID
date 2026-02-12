"""Relevance Engine - Metrics-driven relevance scoring for routes and resources."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .schemas import RelevanceMetrics, RelevanceScore

logger = logging.getLogger(__name__)


class RelevanceEngine:
    """Metrics-driven relevance scoring for routes and resources."""

    def __init__(self):
        """Initialize relevance engine."""
        self._usage_history: dict[str, int] = {}

    def calculate_relevance(
        self,
        route: Path,
        query: str,
        context: dict[str, Any] | None = None,
    ) -> RelevanceScore:
        """Calculate comprehensive relevance score using multiple metrics.

        Args:
            route: Path to score
            query: Query string
            context: Optional context

        Returns:
            RelevanceScore with metrics breakdown
        """
        metrics = RelevanceMetrics(
            semantic_similarity=self._semantic_similarity(route, query),
            path_complexity=self._path_complexity_score(route),
            context_match=self._context_match_score(route, context),
            usage_frequency=self._usage_frequency_score(route),
            integration_alignment=0.5,  # Will be set by integration state manager
        )

        # Weighted combination
        final_score = (
            metrics.semantic_similarity * 0.35
            + (1.0 - metrics.path_complexity) * 0.15
            + metrics.context_match * 0.25
            + metrics.usage_frequency * 0.15
            + metrics.integration_alignment * 0.10
        )

        return RelevanceScore(
            final_score=final_score,
            metrics=metrics,
            confidence=self._calculate_confidence(metrics),
        )

    def _semantic_similarity(self, route: Path, query: str) -> float:
        """Calculate semantic similarity between route and query.

        Args:
            route: Route path
            query: Query string

        Returns:
            Similarity score (0.0 to 1.0)
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Extract words from path
        path_parts = route.parts
        path_words = set()
        for part in path_parts:
            # Split on underscores and hyphens
            words = part.lower().replace("-", "_").split("_")
            path_words.update(w for w in words if len(w) > 2)

        if not path_words:
            return 0.0

        # Calculate Jaccard similarity
        intersection = query_words.intersection(path_words)
        union = query_words.union(path_words)
        similarity = len(intersection) / len(union) if union else 0.0

        # Boost for exact matches
        route_str = str(route).lower()
        for q_word in query_words:
            if q_word in route_str:
                similarity += 0.1

        return min(1.0, similarity)

    def _path_complexity_score(self, route: Path) -> float:
        """Calculate path complexity score.

        Args:
            route: Route path

        Returns:
            Complexity score (0.0 = simple, 1.0 = complex)
        """
        # Depth complexity
        depth = len(route.parts)
        depth_score = min(1.0, depth / 10.0)

        # Name length complexity
        name_length = len(route.name)
        name_score = min(1.0, name_length / 50.0)

        # Combine
        return depth_score * 0.7 + name_score * 0.3

    def _context_match_score(self, route: Path, context: dict[str, Any] | None) -> float:
        """Calculate context match score.

        Args:
            route: Route path
            context: Optional context

        Returns:
            Match score (0.0 to 1.0)
        """
        if not context:
            return 0.5  # Neutral

        context_str = str(context).lower()
        str(route).lower()

        # Check for keyword matches
        matches = 0
        total_checks = 5

        # Check for directory matches
        for part in route.parts:
            if part.lower() in context_str:
                matches += 1

        # Check for file extension matches
        if route.suffix and route.suffix in context_str:
            matches += 1

        return min(1.0, matches / total_checks)

    def _usage_frequency_score(self, route: Path) -> float:
        """Calculate usage frequency score.

        Args:
            route: Route path

        Returns:
            Frequency score (0.0 to 1.0)
        """
        route_str = str(route)
        usage_count = self._usage_history.get(route_str, 0)

        # Normalize usage count (0-10 uses = 0.0-1.0)
        score = min(1.0, usage_count / 10.0)
        return score

    def record_usage(self, route: Path) -> None:
        """Record route usage for frequency scoring.

        Args:
            route: Route path that was used
        """
        route_str = str(route)
        self._usage_history[route_str] = self._usage_history.get(route_str, 0) + 1

    def _calculate_confidence(self, metrics: RelevanceMetrics) -> float:
        """Calculate confidence in relevance score.

        Args:
            metrics: Relevance metrics

        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Higher confidence when metrics are consistent
        metric_values = [
            metrics.semantic_similarity,
            1.0 - metrics.path_complexity,
            metrics.context_match,
            metrics.usage_frequency,
            metrics.integration_alignment,
        ]

        # Calculate variance (lower variance = higher confidence)
        mean = sum(metric_values) / len(metric_values)
        variance = sum((v - mean) ** 2 for v in metric_values) / len(metric_values)
        consistency = 1.0 - min(1.0, variance * 4)  # Scale variance

        # Combine with average score
        avg_score = mean
        confidence = avg_score * 0.6 + consistency * 0.4

        return confidence
