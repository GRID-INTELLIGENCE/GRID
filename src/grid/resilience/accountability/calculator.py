"""Accountability and penalty calculation for endpoint delivery accuracy.

Calculates delivery scores based on success rates, latency, retries, and
data penalties to provide accountability metrics for endpoint performance.

Classification Bands:
    - EXCELLENT (95-100+): Healthy endpoint with bonuses
    - GOOD (80-94): Normal operation
    - DEGRADED (60-79): Performance issues requiring attention
    - CRITICAL (<60): Immediate intervention required

Score Formula:
    Score = 100 - Σ(metric_penalties) - Σ(decayed_data_penalties) + Σ(bonuses)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any

from grid.resilience.metrics import MetricsCollector, OperationMetrics, get_metrics_collector
from grid.resilience.penalties import DataPenaltySchema, calculate_total_penalty

logger = logging.getLogger(__name__)


class DeliveryClassification:
    """Delivery score classification constants."""

    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


@dataclass
class DeliveryScore:
    """Endpoint delivery accountability score.

    Attributes:
        endpoint: The endpoint identifier (e.g., 'GET:/api/v1/search')
        score: Calculated score (0-100+, can exceed 100 with bonuses)
        classification: EXCELLENT, GOOD, DEGRADED, or CRITICAL
        penalties_applied: List of penalties that reduced the score
        bonuses_applied: List of bonuses that increased the score
        timestamp: When the score was calculated
        recommendation: Actionable recommendation based on score
    """

    endpoint: str
    score: float
    classification: str
    penalties_applied: list[dict[str, Any]] = field(default_factory=list)
    bonuses_applied: list[dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the score.
        """
        return {
            "endpoint": self.endpoint,
            "score": round(self.score, 2),
            "classification": self.classification,
            "penalties_applied": self.penalties_applied,
            "bonuses_applied": self.bonuses_applied,
            "timestamp": self.timestamp.isoformat(),
            "recommendation": self.recommendation,
        }


class AccountabilityCalculator:
    """Calculate accountability scores and penalties for endpoint delivery.

    Uses existing MetricsCollector data plus optional data penalties to compute
    delivery scores for endpoints.

    Thresholds (configurable):
        - Success rate < 95%: -10 points
        - Success rate < 90%: -25 points (replaces -10)
        - Fallback rate > 10%: -15 points
        - Avg retries per failure > 2: -8 points
        - Recent error (< 5 min): -5 points

    Bonuses:
        - Perfect streak (> 10 attempts, 0 failures): +5 points
        - Low latency (< 100ms): +3 points
    """

    # SLA Thresholds
    SUCCESS_THRESHOLD_EXCELLENT = 95.0
    SUCCESS_THRESHOLD_GOOD = 90.0
    FALLBACK_THRESHOLD = 10.0
    RETRY_THRESHOLD = 2.0
    ERROR_RECENCY_MINUTES = 5

    # Penalty Points
    PENALTY_LOW_SUCCESS = 10
    PENALTY_CRITICAL_SUCCESS = 25
    PENALTY_HIGH_FALLBACK = 15
    PENALTY_HIGH_RETRIES = 8
    PENALTY_RECENT_ERROR = 5

    # Bonus Points
    BONUS_PERFECT_STREAK = 5
    BONUS_LOW_LATENCY = 3

    # Latency threshold for bonus (milliseconds)
    LOW_LATENCY_THRESHOLD_MS = 100.0

    # Minimum attempts for perfect streak bonus
    PERFECT_STREAK_MIN_ATTEMPTS = 10

    def __init__(
        self,
        metrics_collector: MetricsCollector | None = None,
        half_life_hours: float = 24.0,
    ) -> None:
        """Initialize the accountability calculator.

        Args:
            metrics_collector: Optional MetricsCollector instance.
                Defaults to global collector if not provided.
            half_life_hours: Half-life for data penalty decay (default 24h).
        """
        self._metrics = metrics_collector or get_metrics_collector()
        self._half_life_hours = half_life_hours
        self._history: dict[str, list[DeliveryScore]] = {}
        self._data_penalties: dict[str, list[DataPenaltySchema]] = {}
        self._lock = Lock()

    def register_penalty(self, endpoint: str, penalty: DataPenaltySchema) -> None:
        """Register a data penalty for an endpoint.

        Args:
            endpoint: Endpoint identifier.
            penalty: DataPenaltySchema instance to register.
        """
        with self._lock:
            if endpoint not in self._data_penalties:
                self._data_penalties[endpoint] = []
            self._data_penalties[endpoint].append(penalty)

    def clear_penalties(self, endpoint: str | None = None) -> int:
        """Clear registered penalties.

        Args:
            endpoint: Specific endpoint to clear, or None to clear all.

        Returns:
            Number of penalties cleared.
        """
        with self._lock:
            if endpoint is None:
                count = sum(len(p) for p in self._data_penalties.values())
                self._data_penalties.clear()
                return count
            elif endpoint in self._data_penalties:
                count = len(self._data_penalties[endpoint])
                del self._data_penalties[endpoint]
                return count
            return 0

    def calculate_score(
        self,
        endpoint: str,
        latency_ms: float | None = None,
    ) -> DeliveryScore:
        """Calculate delivery accountability score for an endpoint.

        Args:
            endpoint: Endpoint identifier (e.g., 'GET:/api/v1/search').
            latency_ms: Optional request latency in milliseconds.

        Returns:
            DeliveryScore with calculated score, classification, and details.
        """
        metric = self._metrics.get_operation_metric(endpoint)
        now = datetime.now(UTC)

        penalties: list[dict[str, Any]] = []
        bonuses: list[dict[str, Any]] = []
        score = 100.0

        if metric:
            score, penalties, bonuses = self._apply_metric_adjustments(metric, score, latency_ms, now)

        # Apply latency bonus even without prior metrics
        if latency_ms is not None and latency_ms < self.LOW_LATENCY_THRESHOLD_MS:
            if not any(b.get("type") == "low_latency" for b in bonuses):
                bonuses.append(
                    {
                        "type": "low_latency",
                        "latency_ms": latency_ms,
                        "points": self.BONUS_LOW_LATENCY,
                    }
                )
                score += self.BONUS_LOW_LATENCY

        # Apply data penalties (with decay)
        with self._lock:
            endpoint_penalties = self._data_penalties.get(endpoint, [])
            if endpoint_penalties:
                penalty_points = calculate_total_penalty(endpoint_penalties, now, self._half_life_hours)
                if penalty_points > 0:
                    penalties.append(
                        {
                            "type": "data_penalties",
                            "count": len(endpoint_penalties),
                            "points": -round(penalty_points, 2),
                        }
                    )
                    score -= penalty_points

        # Classification
        classification = self._classify(score)
        recommendation = self._generate_recommendation(penalties, classification)

        score_obj = DeliveryScore(
            endpoint=endpoint,
            score=max(0, score),  # Floor at 0
            classification=classification,
            penalties_applied=penalties,
            bonuses_applied=bonuses,
            timestamp=now,
            recommendation=recommendation,
        )

        # Store history
        with self._lock:
            if endpoint not in self._history:
                self._history[endpoint] = []
            self._history[endpoint].append(score_obj)
            # Limit history size (keep last 1000 per endpoint)
            if len(self._history[endpoint]) > 1000:
                self._history[endpoint] = self._history[endpoint][-1000:]

        return score_obj

    def _apply_metric_adjustments(
        self,
        metric: OperationMetrics,
        score: float,
        latency_ms: float | None,
        now: datetime,
    ) -> tuple[float, list[dict[str, Any]], list[dict[str, Any]]]:
        """Apply penalties and bonuses based on operation metrics.

        Args:
            metric: OperationMetrics for the endpoint.
            score: Starting score.
            latency_ms: Optional latency in milliseconds.
            now: Current timestamp.

        Returns:
            Tuple of (adjusted_score, penalties_list, bonuses_list).
        """
        penalties: list[dict[str, Any]] = []
        bonuses: list[dict[str, Any]] = []

        # Success rate penalties
        success_rate = metric.success_rate()
        if success_rate < self.SUCCESS_THRESHOLD_GOOD:
            penalty = self.PENALTY_CRITICAL_SUCCESS
            penalties.append(
                {
                    "type": "critical_success_rate",
                    "value": round(success_rate, 2),
                    "threshold": self.SUCCESS_THRESHOLD_GOOD,
                    "points": -penalty,
                }
            )
            score -= penalty
        elif success_rate < self.SUCCESS_THRESHOLD_EXCELLENT:
            penalty = self.PENALTY_LOW_SUCCESS
            penalties.append(
                {
                    "type": "low_success_rate",
                    "value": round(success_rate, 2),
                    "threshold": self.SUCCESS_THRESHOLD_EXCELLENT,
                    "points": -penalty,
                }
            )
            score -= penalty

        # Fallback rate penalty
        fallback_rate = metric.fallback_rate()
        if fallback_rate > self.FALLBACK_THRESHOLD:
            penalties.append(
                {
                    "type": "high_fallback_rate",
                    "value": round(fallback_rate, 2),
                    "threshold": self.FALLBACK_THRESHOLD,
                    "points": -self.PENALTY_HIGH_FALLBACK,
                }
            )
            score -= self.PENALTY_HIGH_FALLBACK

        # Retry penalty
        avg_retries = metric.avg_retries_per_failure()
        if avg_retries > self.RETRY_THRESHOLD:
            penalties.append(
                {
                    "type": "high_retry_count",
                    "value": round(avg_retries, 2),
                    "threshold": self.RETRY_THRESHOLD,
                    "points": -self.PENALTY_HIGH_RETRIES,
                }
            )
            score -= self.PENALTY_HIGH_RETRIES

        # Recent error penalty
        if metric.last_error_time:
            error_time = metric.last_error_time
            if error_time.tzinfo is None:
                error_time = error_time.replace(tzinfo=UTC)
            minutes_since = (now - error_time).total_seconds() / 60
            if minutes_since < self.ERROR_RECENCY_MINUTES:
                penalties.append(
                    {
                        "type": "recent_error",
                        "minutes_ago": round(minutes_since, 2),
                        "points": -self.PENALTY_RECENT_ERROR,
                    }
                )
                score -= self.PENALTY_RECENT_ERROR

        # Perfect streak bonus
        if metric.total_attempts >= self.PERFECT_STREAK_MIN_ATTEMPTS and metric.failed_attempts == 0:
            bonuses.append(
                {
                    "type": "perfect_streak",
                    "attempts": metric.total_attempts,
                    "points": self.BONUS_PERFECT_STREAK,
                }
            )
            score += self.BONUS_PERFECT_STREAK

        # Latency bonus
        if latency_ms is not None and latency_ms < self.LOW_LATENCY_THRESHOLD_MS:
            bonuses.append(
                {
                    "type": "low_latency",
                    "latency_ms": latency_ms,
                    "points": self.BONUS_LOW_LATENCY,
                }
            )
            score += self.BONUS_LOW_LATENCY

        return score, penalties, bonuses

    def _classify(self, score: float) -> str:
        """Classify score into delivery tier.

        Args:
            score: Calculated score.

        Returns:
            Classification string.
        """
        if score >= 95:
            return DeliveryClassification.EXCELLENT
        elif score >= 80:
            return DeliveryClassification.GOOD
        elif score >= 60:
            return DeliveryClassification.DEGRADED
        else:
            return DeliveryClassification.CRITICAL

    def _generate_recommendation(self, penalties: list[dict[str, Any]], classification: str) -> str:
        """Generate actionable recommendation based on penalties.

        Args:
            penalties: List of applied penalties.
            classification: Current classification.

        Returns:
            Recommendation string.
        """
        if classification == DeliveryClassification.EXCELLENT:
            return "Maintain current performance. Monitor for regressions."

        critical_penalties = [p for p in penalties if p.get("points", 0) <= -15]
        if critical_penalties:
            top = critical_penalties[0]
            return f"CRITICAL: Address {top['type']} immediately. {len(critical_penalties)} severe issue(s) detected."

        if penalties:
            top = penalties[0]
            value = top.get("value")
            threshold = top.get("threshold")
            if value is not None and threshold is not None:
                return f"Improve {top['type']} (current: {value:.1f}, target: {threshold})."
            return f"Improve {top['type']}."

        return "Review monitoring configuration."

    def get_trend(self, endpoint: str, hours: int = 24) -> dict[str, Any]:
        """Calculate delivery score trend over time.

        Args:
            endpoint: Endpoint identifier.
            hours: Number of hours to analyze (default 24).

        Returns:
            Dictionary with trend analysis:
                - trend: 'improving', 'declining', 'stable', or 'insufficient_data'
                - average_score: Average score over period
                - data_points: Number of scores in period
                - latest_classification: Most recent classification
        """
        with self._lock:
            history = self._history.get(endpoint, [])

        if not history:
            return {"trend": "insufficient_data", "data_points": 0}

        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        recent = [h for h in history if h.timestamp > cutoff]

        if not recent:
            return {"trend": "insufficient_data", "data_points": 0}

        scores = [h.score for h in recent]
        avg_score = sum(scores) / len(scores)

        # Trend direction (compare first half to second half)
        if len(scores) >= 2:
            mid = len(scores) // 2
            first_half = sum(scores[:mid]) / mid if mid > 0 else scores[0]
            second_half = sum(scores[mid:]) / (len(scores) - mid)

            if second_half > first_half + 2:
                trend = "improving"
            elif second_half < first_half - 2:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "average_score": round(avg_score, 2),
            "data_points": len(scores),
            "latest_classification": recent[-1].classification,
        }

    def get_all_scores(self) -> dict[str, DeliveryScore]:
        """Get the latest score for all tracked endpoints.

        Returns:
            Dictionary mapping endpoint to latest DeliveryScore.
        """
        with self._lock:
            return {endpoint: history[-1] for endpoint, history in self._history.items() if history}

    def export_summary(self) -> dict[str, Any]:
        """Export summary of all endpoint scores for monitoring.

        Returns:
            Dictionary with endpoint summaries and aggregates.
        """
        all_scores = self.get_all_scores()

        if not all_scores:
            return {
                "timestamp": datetime.now(UTC).isoformat(),
                "total_endpoints": 0,
                "endpoints": {},
            }

        endpoint_summaries = {}
        total_score = 0.0

        for endpoint, score in all_scores.items():
            endpoint_summaries[endpoint] = {
                "score": score.score,
                "classification": score.classification,
                "timestamp": score.timestamp.isoformat(),
            }
            total_score += score.score

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_endpoints": len(all_scores),
            "average_score": round(total_score / len(all_scores), 2),
            "endpoints": endpoint_summaries,
        }


# Global calculator instance
_global_calculator: AccountabilityCalculator | None = None


def get_accountability_calculator() -> AccountabilityCalculator:
    """Get the global accountability calculator instance.

    Returns:
        The global AccountabilityCalculator instance (lazy-initialized).
    """
    global _global_calculator
    if _global_calculator is None:
        _global_calculator = AccountabilityCalculator()
    return _global_calculator


__all__ = [
    "DeliveryClassification",
    "DeliveryScore",
    "AccountabilityCalculator",
    "get_accountability_calculator",
]
