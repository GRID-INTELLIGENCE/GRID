"""
Adaptive Learning - Machine Learning Feedback Loop.

Provides adaptive learning capabilities:
- Performance tracking and history
- Outcome-based learning
- Adaptive rate adjustment
- Model improvement suggestions
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class LearningSignal(Enum):
    """Types of learning signals."""

    POSITIVE = "positive"  # Correct prediction/decision
    NEGATIVE = "negative"  # Incorrect prediction/decision
    NEUTRAL = "neutral"  # No clear signal
    FEEDBACK = "feedback"  # Explicit user feedback


class OutcomeType(Enum):
    """Types of outcomes for learning."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class LearningOutcome:
    """Represents a learning outcome for feedback."""

    outcome_id: str
    outcome_type: OutcomeType
    signal: LearningSignal
    input_features: dict[str, Any]
    predicted_output: Any
    actual_output: Any | None = None
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "outcome_id": self.outcome_id,
            "outcome_type": self.outcome_type.value,
            "signal": self.signal.value,
            "predicted_output": self.predicted_output,
            "actual_output": self.actual_output,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for learning system."""

    total_predictions: int = 0
    correct_predictions: int = 0
    incorrect_predictions: int = 0
    partial_predictions: int = 0
    avg_confidence: float = 0.0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0

    def update(self, outcome: LearningOutcome) -> None:
        """Update metrics from outcome."""
        self.total_predictions += 1

        if outcome.signal == LearningSignal.POSITIVE:
            self.correct_predictions += 1
        elif outcome.signal == LearningSignal.NEGATIVE:
            self.incorrect_predictions += 1
        else:
            self.partial_predictions += 1

        # Update accuracy
        if self.total_predictions > 0:
            self.accuracy = self.correct_predictions / self.total_predictions

        # Update average confidence (exponential moving average)
        alpha = 0.1
        self.avg_confidence = alpha * outcome.confidence + (1 - alpha) * self.avg_confidence

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_predictions": self.total_predictions,
            "correct_predictions": self.correct_predictions,
            "incorrect_predictions": self.incorrect_predictions,
            "partial_predictions": self.partial_predictions,
            "avg_confidence": self.avg_confidence,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
        }


class AdaptiveLearning:
    """
    Adaptive Learning System.

    Implements a feedback loop for:
    - Learning from outcomes
    - Adjusting prediction confidence
    - Tracking performance over time
    - Suggesting model improvements
    """

    def __init__(
        self,
        adaptation_rate: float = 0.1,
        memory_size: int = 1000,
    ):
        self._adaptation_rate = adaptation_rate
        self._memory_size = memory_size

        # Performance tracking
        self._performance = PerformanceMetrics()
        self._performance_history: list[LearningOutcome] = []

        # Feature importance tracking
        self._feature_importance: dict[str, float] = defaultdict(lambda: 1.0)
        self._feature_performance: dict[str, PerformanceMetrics] = {}

        # Learning state
        self._is_learning = True
        self._min_samples = 10  # Minimum samples before adapting

        # Callbacks
        self._on_improvement: list[Callable[[dict[str, Any]], None]] = []
        self._on_degradation: list[Callable[[dict[str, Any]], None]] = []

        # Stats
        self._stats = defaultdict(int)

    @property
    def is_learning(self) -> bool:
        """Check if learning is enabled."""
        return self._is_learning

    @property
    def adaptation_rate(self) -> float:
        """Get current adaptation rate."""
        return self._adaptation_rate

    def learn_from_outcome(self, input_data: Any, outcome: LearningOutcome) -> None:
        """
        Learn from a prediction outcome.

        Args:
            input_data: Original input data
            outcome: The outcome of the prediction
        """
        if not self._is_learning:
            return

        # Record outcome
        self._performance_history.append(outcome)
        if len(self._performance_history) > self._memory_size:
            self._performance_history.pop(0)

        # Update performance metrics
        old_accuracy = self._performance.accuracy
        self._performance.update(outcome)

        # Update feature importance
        self._update_feature_importance(outcome)

        # Check for improvement or degradation
        if self._performance.total_predictions >= self._min_samples:
            self._check_performance_change(old_accuracy)

        self._stats["outcomes_processed"] += 1

        logger.debug(
            f"Learning from outcome: {outcome.outcome_type.value}, "
            f"signal: {outcome.signal.value}, "
            f"accuracy: {self._performance.accuracy:.3f}"
        )

    def _update_feature_importance(self, outcome: LearningOutcome) -> None:
        """Update feature importance based on outcome."""
        for feature_name, _feature_value in outcome.input_features.items():
            if feature_name not in self._feature_performance:
                self._feature_performance[feature_name] = PerformanceMetrics()

            self._feature_performance[feature_name].update(outcome)

            # Adjust importance based on feature's contribution to accuracy
            feature_accuracy = self._feature_performance[feature_name].accuracy
            overall_accuracy = self._performance.accuracy

            if feature_accuracy > overall_accuracy:
                # Feature contributes positively
                self._feature_importance[feature_name] *= 1 + self._adaptation_rate
            elif feature_accuracy < overall_accuracy:
                # Feature contributes negatively
                self._feature_importance[feature_name] *= 1 - (self._adaptation_rate / 2)

            # Clamp importance
            self._feature_importance[feature_name] = max(0.1, min(10.0, self._feature_importance[feature_name]))

    def _check_performance_change(self, old_accuracy: float) -> None:
        """Check for significant performance changes."""
        new_accuracy = self._performance.accuracy
        change = new_accuracy - old_accuracy

        if change > 0.05:  # 5% improvement
            self._stats["improvements"] += 1
            for callback in self._on_improvement:
                try:
                    callback(
                        {
                            "old_accuracy": old_accuracy,
                            "new_accuracy": new_accuracy,
                            "change": change,
                        }
                    )
                except Exception as e:
                    logger.error(f"Improvement callback error: {e}")

        elif change < -0.05:  # 5% degradation
            self._stats["degradations"] += 1
            for callback in self._on_degradation:
                try:
                    callback(
                        {
                            "old_accuracy": old_accuracy,
                            "new_accuracy": new_accuracy,
                            "change": change,
                        }
                    )
                except Exception as e:
                    logger.error(f"Degradation callback error: {e}")

    def get_adjusted_confidence(self, base_confidence: float, features: dict[str, Any]) -> float:
        """
        Get confidence adjusted by feature importance.

        Args:
            base_confidence: Original confidence score
            features: Feature dictionary

        Returns:
            Adjusted confidence score
        """
        if not features:
            return base_confidence

        total_importance = 0.0
        weighted_confidence = 0.0

        for feature_name in features:
            importance = self._feature_importance.get(feature_name, 1.0)
            total_importance += importance
            weighted_confidence += importance * base_confidence

        if total_importance > 0:
            adjusted = weighted_confidence / total_importance
        else:
            adjusted = base_confidence

        # Apply historical accuracy as a modifier
        if self._performance.total_predictions >= self._min_samples:
            adjusted *= 0.5 + (0.5 * self._performance.accuracy)

        return max(0.0, min(1.0, adjusted))

    def suggest_improvements(self) -> list[dict[str, Any]]:
        """
        Generate suggestions for model improvement.

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Check overall accuracy
        if self._performance.accuracy < 0.7:
            suggestions.append(
                {
                    "type": "accuracy_low",
                    "severity": "high",
                    "message": "Overall accuracy below 70%",
                    "recommendation": "Review training data and feature engineering",
                }
            )

        # Check for underperforming features
        for feature_name, metrics in self._feature_performance.items():
            if metrics.accuracy < self._performance.accuracy - 0.1:
                suggestions.append(
                    {
                        "type": "feature_underperforming",
                        "severity": "medium",
                        "feature": feature_name,
                        "feature_accuracy": metrics.accuracy,
                        "message": f"Feature '{feature_name}' underperforming",
                        "recommendation": "Consider removing or transforming this feature",
                    }
                )

        # Check for low confidence
        if self._performance.avg_confidence < 0.5:
            suggestions.append(
                {
                    "type": "confidence_low",
                    "severity": "medium",
                    "message": "Average confidence below 50%",
                    "recommendation": "Model may need more training data",
                }
            )

        # Check sample size
        if self._performance.total_predictions < self._min_samples * 2:
            suggestions.append(
                {
                    "type": "small_sample",
                    "severity": "info",
                    "message": f"Only {self._performance.total_predictions} samples collected",
                    "recommendation": "Continue collecting data for more reliable metrics",
                }
            )

        return suggestions

    def on_improvement(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """Register callback for performance improvement."""
        self._on_improvement.append(callback)

    def on_degradation(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """Register callback for performance degradation."""
        self._on_degradation.append(callback)

    def enable_learning(self, enabled: bool = True) -> None:
        """Enable or disable learning."""
        self._is_learning = enabled

    def set_adaptation_rate(self, rate: float) -> None:
        """Set the adaptation rate."""
        self._adaptation_rate = max(0.01, min(1.0, rate))

    def get_feature_importance(self) -> dict[str, float]:
        """Get current feature importance scores."""
        return dict(self._feature_importance)

    def get_performance(self) -> dict[str, Any]:
        """Get current performance metrics."""
        return self._performance.to_dict()

    def get_stats(self) -> dict[str, Any]:
        """Get learning statistics."""
        return {
            **dict(self._stats),
            "is_learning": self._is_learning,
            "adaptation_rate": self._adaptation_rate,
            "memory_size": self._memory_size,
            "samples_collected": len(self._performance_history),
            "features_tracked": len(self._feature_importance),
        }

    def get_recent_outcomes(self, count: int = 20) -> list[dict[str, Any]]:
        """Get recent learning outcomes."""
        return [o.to_dict() for o in self._performance_history[-count:]]

    def reset(self) -> None:
        """Reset learning state."""
        self._performance = PerformanceMetrics()
        self._performance_history.clear()
        self._feature_importance.clear()
        self._feature_performance.clear()
        self._stats.clear()
        logger.info("Adaptive learning system reset")


# Singleton instance
_learner: AdaptiveLearning | None = None


def get_adaptive_learner() -> AdaptiveLearning:
    """Get the singleton AdaptiveLearning instance."""
    global _learner
    if _learner is None:
        _learner = AdaptiveLearning()
    return _learner
