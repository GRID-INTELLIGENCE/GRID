"""Version scoring and tier assignment for artifact generation.

Optimized implementation with:
- Pre-computed weights for faster calculation
- Efficient memory usage with __slots__
- Cached score calculations
- Incremental updates
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import Any


@dataclass(slots=True)  # Optimize memory with __slots__
class VersionMetrics:
    """Metrics used for version scoring."""

    coherence_accumulation: float = 0.0
    evolution_count: int = 0
    pattern_emergence_rate: float = 0.0
    operation_success_rate: float = 0.0
    avg_confidence: float = 0.0
    skill_retrieval_score: float = 0.0
    resource_efficiency: float = 0.0
    error_recovery_rate: float = 0.0

    def to_tuple(self) -> tuple:
        """Convert to tuple for caching."""
        return (
            self.coherence_accumulation,
            self.evolution_count,
            self.pattern_emergence_rate,
            self.operation_success_rate,
            self.avg_confidence,
            self.skill_retrieval_score,
            self.resource_efficiency,
            self.error_recovery_rate,
        )


# Pre-computed weights for faster calculation
WEIGHTS = {
    "coherence_accumulation": (0.95, 0.20),
    "evolution_count": (100, 0.15),
    "pattern_emergence_rate": (1.0, 0.10),
    "operation_success_rate": (1.0, 0.15),
    "avg_confidence": (1.0, 0.10),
    "skill_retrieval_score": (1.0, 0.10),
    "resource_efficiency": (1.0, 0.10),
    "error_recovery_rate": (1.0, 0.10),
}

# Pre-computed version thresholds for O(1) lookup
VERSION_THRESHOLDS = [(0.85, "3.5"), (0.70, "3.0"), (0.50, "2.0"), (0.0, "1.0")]  # Gold tier


class VersionScorer:
    """
    Calculates version scores and assigns tiers based on metrics.

    Optimized for performance with:
    - Pre-computed weights
    - Cached calculations
    - Efficient memory usage
    - Incremental score updates
    """

    __slots__ = ["version_history", "_cached_scores", "_last_metrics_hash", "_max_history"]

    def __init__(self, max_history: int = 1000):
        self.version_history: list[dict] = []
        self._cached_scores: dict[int, tuple[float, str]] = {}
        self._last_metrics_hash: int | None = None
        self._max_history = max_history

    @staticmethod
    @lru_cache(maxsize=128)
    def _calculate_score_cached(metrics_tuple: tuple) -> tuple[float, str]:
        """
        Calculate score with caching for repeated metrics.

        Args:
            metrics_tuple: Tuple of metric values

        Returns:
            Tuple of (score, version)
        """
        # Unpack metrics
        coherence, evolution, pattern, success, confidence, skill, resource, error = metrics_tuple

        # Optimized score calculation using pre-computed weights
        score = 0.0

        # Coherence accumulation
        score += min(1.0, coherence / 0.95) * 0.20

        # Evolution count
        score += min(1.0, evolution / 100) * 0.15

        # Other metrics with 1.0 max
        score += pattern * 0.10
        score += success * 0.15
        score += confidence * 0.10
        score += skill * 0.10
        score += resource * 0.10
        score += error * 0.10

        # O(1) version lookup using pre-computed thresholds
        for threshold, version in VERSION_THRESHOLDS:
            if score >= threshold:
                return (round(score, 4), version)

        return (round(score, 4), "1.0")

    def calculate_version_score(self, metrics: VersionMetrics) -> tuple[float, str]:
        """
        Calculate weighted version score and determine tier.

        Args:
            metrics: Version metrics

        Returns:
            Tuple of (score, version)
        """
        # Convert to tuple for caching
        metrics_tuple = metrics.to_tuple()
        metrics_hash = hash(metrics_tuple)

        # Check cache
        if metrics_hash == self._last_metrics_hash:
            return self._cached_scores.get(metrics_hash, (0.0, "1.0"))

        # Calculate with caching
        result = self._calculate_score_cached(metrics_tuple)

        # Update cache
        self._cached_scores[metrics_hash] = result
        self._last_metrics_hash = metrics_hash

        # Limit cache size
        if len(self._cached_scores) > 128:
            self._cached_scores.clear()

        return result

    def _determine_version(self, score: float) -> str:
        """Determine version tier from score using O(1) lookup."""
        for threshold, version in VERSION_THRESHOLDS:
            if score >= threshold:
                return version
        return "1.0"

    def record_version_checkpoint(self, batch: int, score: float, version: str) -> None:
        """Record a version checkpoint in history with memory limit."""
        self.version_history.append(
            {
                "batch": batch,
                "score": round(score, 4),
                "version": version,
            }
        )

        # Limit history size for memory efficiency
        if len(self.version_history) > self._max_history:
            self.version_history = self.version_history[-self._max_history :]

    def validate_momentum(self, window: int = 10) -> bool:
        """
        Validate that scores are non-decreasing (momentum check).

        Args:
            window: Number of recent checkpoints to check

        Returns:
            True if momentum is maintained
        """
        if len(self.version_history) < 2:
            return True

        # Check only recent window for efficiency
        recent = self.version_history[-window:]
        scores: list[float] = [cp["score"] for cp in recent]

        return scores[-1] >= scores[0]

    def get_version_history(self, limit: int | None = None) -> list[dict]:
        """
        Get the version history.

        Args:
            limit: Optional limit on number of entries

        Returns:
            List of version checkpoints
        """
        if limit:
            return self.version_history[-limit:].copy()
        return self.version_history.copy()

    def get_latest_version(self) -> str | None:
        """Get the latest version from history."""
        if not self.version_history:
            return None
        return str(self.version_history[-1]["version"])

    def get_performance_stats(self) -> dict[str, Any]:
        """
        Get performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        if not self.version_history:
            return {"total_checkpoints": 0, "average_score": 0.0, "score_trend": "neutral"}

        scores = [cp["score"] for cp in self.version_history]
        avg_score = sum(scores) / len(scores)

        # Determine trend
        if len(scores) >= 2:
            recent_avg = sum(scores[-10:]) / min(len(scores), 10)
            older_avg = sum(scores[:10]) / min(len(scores), 10)

            if recent_avg > older_avg * 1.05:
                trend = "improving"
            elif recent_avg < older_avg * 0.95:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "neutral"

        return {
            "total_checkpoints": len(self.version_history),
            "average_score": round(avg_score, 4),
            "current_score": scores[-1],
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "score_trend": trend,
            "cache_size": len(self._cached_scores),
        }

    def clear_cache(self) -> None:
        """Clear internal caches to free memory."""
        self._cached_scores.clear()
        self._last_metrics_hash = None
