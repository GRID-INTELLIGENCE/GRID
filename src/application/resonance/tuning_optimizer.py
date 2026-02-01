"""
Resonance Tuning Optimizer - Dynamic Parameter Tuning.

Maps analytics insights to specific parameter adjustments with:
- Insight-to-parameter mapping
- A/B testing framework
- Recommendation validation
- Confidence scoring
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

from .analytics_service import (
    AlertSeverity,
    AnalyticsInsight,
    InsightType,
)

logger = logging.getLogger(__name__)


class TuningParameter(str, Enum):
    """Tunable system parameters."""

    ATTACK_TIME = "attack_time"
    DECAY_TIME = "decay_time"
    SUSTAIN_LEVEL = "sustain_level"
    RELEASE_TIME = "release_time"
    BATCH_SIZE = "batch_size"
    TICK_RATE = "tick_rate"
    QUEUE_DEPTH = "queue_depth"
    WORKER_COUNT = "worker_count"
    IMPACT_THRESHOLD = "impact_threshold"


class RecommendationStatus(str, Enum):
    """Status of a tuning recommendation."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ParameterValue:
    """Current and recommended parameter value."""

    parameter: TuningParameter
    current_value: float
    recommended_value: float
    min_value: float
    max_value: float
    unit: str = ""


@dataclass
class TuningRecommendation:
    """A parameter tuning recommendation."""

    id: str
    insight_id: str
    parameter: TuningParameter
    current_value: float
    recommended_value: float
    rationale: str
    confidence: float  # 0.0 to 1.0
    expected_improvement: str
    status: RecommendationStatus = RecommendationStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    applied_at: datetime | None = None
    approved_by: str | None = None
    before_metrics: dict[str, Any] = field(default_factory=dict)
    after_metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class ABTestResult:
    """Result of an A/B test for a parameter change."""

    test_id: str
    recommendation_id: str
    parameter: TuningParameter
    control_value: float
    variant_value: float
    start_time: datetime
    end_time: datetime | None
    control_metrics: dict[str, float]
    variant_metrics: dict[str, float]
    winner: str | None = None  # "control", "variant", or None
    confidence_level: float = 0.0
    is_complete: bool = False


@dataclass
class TuningHistory:
    """Historical record of a tuning change."""

    id: str
    recommendation_id: str
    parameter: TuningParameter
    old_value: float
    new_value: float
    applied_at: datetime
    applied_by: str
    result: str  # "positive", "negative", "neutral"
    metrics_before: dict[str, float]
    metrics_after: dict[str, float]
    notes: str = ""


class TuningOptimizer:
    """
    Dynamic Tuning Optimizer for Resonance Parameters.

    Maps insights to parameter adjustments:
    - High spike frequency → reduce attack_time
    - Low efficiency → increase batch_size
    - High latency → increase worker_count
    - Imbalance → adjust sampling rates
    """

    # Parameter mapping: insight_type → (parameter, adjustment_direction, magnitude)
    INSIGHT_PARAMETER_MAP: dict[InsightType, list[tuple[TuningParameter, str, float]]] = {
        InsightType.SPIKE_DETECTED: [
            (TuningParameter.ATTACK_TIME, "decrease", 0.1),
            (TuningParameter.IMPACT_THRESHOLD, "increase", 0.05),
        ],
        InsightType.IMBALANCE: [
            (TuningParameter.BATCH_SIZE, "increase", 10),
            (TuningParameter.TICK_RATE, "decrease", 5),
        ],
        InsightType.EFFICIENCY_DROP: [
            (TuningParameter.BATCH_SIZE, "increase", 20),
            (TuningParameter.WORKER_COUNT, "increase", 1),
            (TuningParameter.QUEUE_DEPTH, "increase", 100),
        ],
        InsightType.ANOMALY: [
            (TuningParameter.IMPACT_THRESHOLD, "decrease", 0.05),
        ],
    }

    # Default parameter values and bounds
    DEFAULT_PARAMETERS: dict[TuningParameter, dict[str, float]] = {
        TuningParameter.ATTACK_TIME: {"default": 0.1, "min": 0.01, "max": 1.0},
        TuningParameter.DECAY_TIME: {"default": 0.2, "min": 0.05, "max": 2.0},
        TuningParameter.SUSTAIN_LEVEL: {"default": 0.7, "min": 0.1, "max": 1.0},
        TuningParameter.RELEASE_TIME: {"default": 0.3, "min": 0.1, "max": 3.0},
        TuningParameter.BATCH_SIZE: {"default": 100, "min": 10, "max": 1000},
        TuningParameter.TICK_RATE: {"default": 60, "min": 10, "max": 120},
        TuningParameter.QUEUE_DEPTH: {"default": 1000, "min": 100, "max": 10000},
        TuningParameter.WORKER_COUNT: {"default": 4, "min": 1, "max": 16},
        TuningParameter.IMPACT_THRESHOLD: {"default": 0.5, "min": 0.1, "max": 0.95},
    }

    # Confidence thresholds
    AUTO_APPLY_CONFIDENCE = 0.9  # Auto-apply if confidence >= 90%
    MIN_RECOMMENDATION_CONFIDENCE = 0.5  # Don't recommend below 50%

    def __init__(
        self,
        get_current_value: Callable[[TuningParameter], float] | None = None,
        apply_value: Callable[[TuningParameter, float], bool] | None = None,
    ):
        """
        Initialize the Tuning Optimizer.

        Args:
            get_current_value: Callback to get current parameter value
            apply_value: Callback to apply a new parameter value
        """
        self._get_current_value = get_current_value or self._default_get_value
        self._apply_value = apply_value or self._default_apply_value

        # State
        self._current_values: dict[TuningParameter, float] = {
            p: self.DEFAULT_PARAMETERS[p]["default"] for p in TuningParameter
        }
        self._recommendations: list[TuningRecommendation] = []
        self._ab_tests: list[ABTestResult] = []
        self._history: list[TuningHistory] = []

        # Confidence scoring based on historical accuracy
        self._recommendation_success_count: int = 0
        self._recommendation_total_count: int = 0

    def _default_get_value(self, param: TuningParameter) -> float:
        """Default implementation: return from internal state."""
        return self._current_values.get(param, self.DEFAULT_PARAMETERS[param]["default"])

    def _default_apply_value(self, param: TuningParameter, value: float) -> bool:
        """Default implementation: update internal state."""
        self._current_values[param] = value
        return True

    def generate_recommendations(
        self,
        insight: AnalyticsInsight,
    ) -> list[TuningRecommendation]:
        """
        Generate tuning recommendations based on an analytics insight.

        Args:
            insight: The analytics insight to process

        Returns:
            List of tuning recommendations
        """
        recommendations: list[TuningRecommendation] = []

        mappings = self.INSIGHT_PARAMETER_MAP.get(insight.insight_type, [])

        for param, direction, magnitude in mappings:
            current = self._get_current_value(param)
            bounds = self.DEFAULT_PARAMETERS[param]

            # Calculate recommended value
            if direction == "increase":
                recommended = min(current + magnitude, bounds["max"])
            else:
                recommended = max(current - magnitude, bounds["min"])

            # Skip if no change needed
            if abs(recommended - current) < 0.001:
                continue

            # Calculate confidence based on insight severity and historical accuracy
            base_confidence = {
                AlertSeverity.CRITICAL: 0.85,
                AlertSeverity.WARNING: 0.70,
                AlertSeverity.INFO: 0.55,
            }.get(insight.severity, 0.60)

            # Adjust confidence by historical success rate
            if self._recommendation_total_count > 10:
                historical_rate = self._recommendation_success_count / self._recommendation_total_count
                base_confidence = base_confidence * 0.6 + historical_rate * 0.4

            # Don't recommend if confidence too low
            if base_confidence < self.MIN_RECOMMENDATION_CONFIDENCE:
                continue

            recommendation = TuningRecommendation(
                id=f"REC-{uuid4().hex[:8].upper()}",
                insight_id=insight.id,
                parameter=param,
                current_value=current,
                recommended_value=recommended,
                rationale=self._generate_rationale(insight, param, direction, magnitude),
                confidence=base_confidence,
                expected_improvement=self._generate_improvement_desc(insight, param, direction),
            )

            recommendations.append(recommendation)
            self._recommendations.append(recommendation)

        logger.info(f"Generated {len(recommendations)} recommendations for insight {insight.id}")
        return recommendations

    def _generate_rationale(
        self,
        insight: AnalyticsInsight,
        param: TuningParameter,
        direction: str,
        magnitude: float,
    ) -> str:
        """Generate human-readable rationale for a recommendation."""
        # Safely extract metrics with proper fallbacks
        avg_density = insight.metrics.get("avg_density")
        efficiency = insight.metrics.get("efficiency")
        dominant_ratio = insight.metrics.get("dominant_ratio")

        # Format metrics safely
        density_str = f"{avg_density}/min" if avg_density is not None else "elevated"
        efficiency_str = f"{efficiency*100:.1f}%" if efficiency is not None else "below threshold"
        ratio_str = f"{dominant_ratio*100:.1f}%" if dominant_ratio is not None else "imbalanced"

        rationales = {
            (
                InsightType.SPIKE_DETECTED,
                TuningParameter.ATTACK_TIME,
            ): f"High spike frequency detected ({density_str}). "
            f"Reducing attack_time by {magnitude} will smooth response curves.",
            (
                InsightType.SPIKE_DETECTED,
                TuningParameter.IMPACT_THRESHOLD,
            ): f"Frequent high-impact spikes suggest the threshold should be raised to {magnitude} "
            f"to filter noise and focus on critical events.",
            (InsightType.EFFICIENCY_DROP, TuningParameter.BATCH_SIZE): f"System efficiency at {efficiency_str}. "
            f"Increasing batch size by {magnitude} reduces per-event overhead.",
            (
                InsightType.EFFICIENCY_DROP,
                TuningParameter.WORKER_COUNT,
            ): f"Processing backlog detected. Adding {int(magnitude)} worker(s) will improve throughput.",
            (InsightType.IMBALANCE, TuningParameter.BATCH_SIZE): f"Event type imbalance at {ratio_str}. "
            f"Larger batches help normalize sampling distribution.",
        }

        key = (insight.insight_type, param)
        return rationales.get(key, f"{direction.capitalize()} {param.value} based on {insight.insight_type.value}")

    def _generate_improvement_desc(
        self,
        insight: AnalyticsInsight,
        param: TuningParameter,
        direction: str,
    ) -> str:
        """Generate expected improvement description."""
        improvements = {
            (InsightType.SPIKE_DETECTED, TuningParameter.ATTACK_TIME): "Smoother spike response, reduced alert fatigue",
            (
                InsightType.SPIKE_DETECTED,
                TuningParameter.IMPACT_THRESHOLD,
            ): "Fewer false-positive alerts, clearer signal",
            (InsightType.EFFICIENCY_DROP, TuningParameter.BATCH_SIZE): "~15-25% reduction in cost per meaningful event",
            (InsightType.EFFICIENCY_DROP, TuningParameter.WORKER_COUNT): "~20% improvement in processing throughput",
            (InsightType.IMBALANCE, TuningParameter.BATCH_SIZE): "Better modality balance, improved data quality",
        }

        key = (insight.insight_type, param)
        return improvements.get(key, f"Improved {param.value} performance")

    def approve_recommendation(
        self,
        recommendation_id: str,
        approver_id: str,
    ) -> TuningRecommendation | None:
        """
        Approve a tuning recommendation (HITL).

        Args:
            recommendation_id: ID of the recommendation to approve
            approver_id: ID of the approving user

        Returns:
            Updated recommendation or None if not found
        """
        for rec in self._recommendations:
            if rec.id == recommendation_id:
                rec.status = RecommendationStatus.APPROVED
                rec.approved_by = approver_id
                logger.info(f"Recommendation {recommendation_id} approved by {approver_id}")
                return rec
        return None

    def reject_recommendation(
        self,
        recommendation_id: str,
        reason: str = "",
    ) -> TuningRecommendation | None:
        """Reject a tuning recommendation."""
        for rec in self._recommendations:
            if rec.id == recommendation_id:
                rec.status = RecommendationStatus.REJECTED
                logger.info(f"Recommendation {recommendation_id} rejected: {reason}")
                return rec
        return None

    async def apply_recommendation(
        self,
        recommendation_id: str,
        current_metrics: dict[str, float],
    ) -> bool:
        """
        Apply an approved tuning recommendation.

        Args:
            recommendation_id: ID of the recommendation to apply
            current_metrics: Current system metrics for before/after comparison

        Returns:
            True if successfully applied
        """
        rec = None
        for r in self._recommendations:
            if r.id == recommendation_id:
                rec = r
                break

        if not rec:
            logger.warning(f"Recommendation {recommendation_id} not found")
            return False

        if rec.status != RecommendationStatus.APPROVED:
            logger.warning(f"Recommendation {recommendation_id} not approved (status: {rec.status})")
            return False

        # Store before metrics
        rec.before_metrics = current_metrics.copy()

        # Apply the change
        success = self._apply_value(rec.parameter, rec.recommended_value)

        if success:
            rec.status = RecommendationStatus.APPLIED
            rec.applied_at = datetime.now(UTC)

            # Record history
            history = TuningHistory(
                id=f"HIST-{uuid4().hex[:8].upper()}",
                recommendation_id=rec.id,
                parameter=rec.parameter,
                old_value=rec.current_value,
                new_value=rec.recommended_value,
                applied_at=rec.applied_at,
                applied_by=rec.approved_by or "system",
                result="pending",
                metrics_before=rec.before_metrics,
                metrics_after={},
            )
            self._history.append(history)

            logger.info(f"Applied recommendation {recommendation_id}: {rec.parameter.value} = {rec.recommended_value}")
        else:
            rec.status = RecommendationStatus.FAILED
            logger.error(f"Failed to apply recommendation {recommendation_id}")

        return success

    async def evaluate_recommendation(
        self,
        recommendation_id: str,
        after_metrics: dict[str, float],
    ) -> str | None:
        """
        Evaluate the result of an applied recommendation.

        Args:
            recommendation_id: ID of the recommendation
            after_metrics: Metrics after the change was applied

        Returns:
            Result: "positive", "negative", or "neutral"
        """
        rec = None
        for r in self._recommendations:
            if r.id == recommendation_id:
                rec = r
                break

        if not rec or rec.status != RecommendationStatus.APPLIED:
            return None

        rec.after_metrics = after_metrics.copy()

        # Find corresponding history entry
        for hist in self._history:
            if hist.recommendation_id == recommendation_id:
                hist.metrics_after = after_metrics.copy()

                # Evaluate improvement
                before_efficiency = rec.before_metrics.get("efficiency", 0.5)
                after_efficiency = after_metrics.get("efficiency", 0.5)

                if after_efficiency > before_efficiency * 1.1:  # >10% improvement
                    hist.result = "positive"
                    self._recommendation_success_count += 1
                elif after_efficiency < before_efficiency * 0.9:  # >10% degradation
                    hist.result = "negative"
                else:
                    hist.result = "neutral"

                self._recommendation_total_count += 1

                logger.info(f"Recommendation {recommendation_id} evaluation: {hist.result}")
                return hist.result

        return None

    async def rollback_recommendation(
        self,
        recommendation_id: str,
    ) -> bool:
        """
        Rollback an applied recommendation to the previous value.

        Args:
            recommendation_id: ID of the recommendation to rollback

        Returns:
            True if successfully rolled back
        """
        rec = None
        for r in self._recommendations:
            if r.id == recommendation_id:
                rec = r
                break

        if not rec or rec.status != RecommendationStatus.APPLIED:
            return False

        # Apply the old value
        success = self._apply_value(rec.parameter, rec.current_value)

        if success:
            rec.status = RecommendationStatus.ROLLED_BACK

            for hist in self._history:
                if hist.recommendation_id == recommendation_id:
                    hist.notes = "Rolled back"
                    break

            logger.info(f"Rolled back recommendation {recommendation_id}")

        return success

    def start_ab_test(
        self,
        recommendation_id: str,
        duration_minutes: int = 60,
    ) -> ABTestResult | None:
        """
        Start an A/B test for a recommendation.

        Args:
            recommendation_id: ID of the recommendation to test
            duration_minutes: Duration of the test

        Returns:
            A/B test result object
        """
        rec = None
        for r in self._recommendations:
            if r.id == recommendation_id:
                rec = r
                break

        if not rec:
            return None

        test = ABTestResult(
            test_id=f"TEST-{uuid4().hex[:8].upper()}",
            recommendation_id=recommendation_id,
            parameter=rec.parameter,
            control_value=rec.current_value,
            variant_value=rec.recommended_value,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC) + timedelta(minutes=duration_minutes),
            control_metrics={},
            variant_metrics={},
        )

        self._ab_tests.append(test)
        logger.info(f"Started A/B test {test.test_id} for recommendation {recommendation_id}")

        return test

    def complete_ab_test(
        self,
        test_id: str,
        control_metrics: dict[str, float],
        variant_metrics: dict[str, float],
    ) -> ABTestResult | None:
        """
        Complete an A/B test with collected metrics.

        Args:
            test_id: ID of the test
            control_metrics: Metrics from the control group
            variant_metrics: Metrics from the variant group

        Returns:
            Completed A/B test result
        """
        for test in self._ab_tests:
            if test.test_id == test_id:
                test.control_metrics = control_metrics
                test.variant_metrics = variant_metrics
                test.end_time = datetime.now(UTC)
                test.is_complete = True

                # Determine winner based on efficiency metric
                control_eff = control_metrics.get("efficiency", 0.5)
                variant_eff = variant_metrics.get("efficiency", 0.5)

                if variant_eff > control_eff * 1.05:  # >5% improvement
                    test.winner = "variant"
                    test.confidence_level = min(0.95, 0.7 + (variant_eff - control_eff) * 2)
                elif control_eff > variant_eff * 1.05:
                    test.winner = "control"
                    test.confidence_level = min(0.95, 0.7 + (control_eff - variant_eff) * 2)
                else:
                    test.winner = None
                    test.confidence_level = 0.0

                logger.info(
                    f"Completed A/B test {test_id}: winner={test.winner}, confidence={test.confidence_level:.2f}"
                )
                return test

        return None

    def get_recommendations(
        self,
        status: RecommendationStatus | None = None,
        limit: int = 50,
    ) -> list[TuningRecommendation]:
        """Get recommendations with optional status filter."""
        recs = self._recommendations.copy()
        if status:
            recs = [r for r in recs if r.status == status]
        return recs[-limit:]

    def get_history(self, limit: int = 100) -> list[TuningHistory]:
        """Get tuning history."""
        return self._history[-limit:]

    def get_ab_tests(self, complete_only: bool = False) -> list[ABTestResult]:
        """Get A/B test results."""
        tests = self._ab_tests.copy()
        if complete_only:
            tests = [t for t in tests if t.is_complete]
        return tests

    def get_current_parameters(self) -> dict[str, ParameterValue]:
        """Get all current parameter values with metadata."""
        return {
            p.value: ParameterValue(
                parameter=p,
                current_value=self._get_current_value(p),
                recommended_value=self._get_current_value(p),  # No pending change
                min_value=self.DEFAULT_PARAMETERS[p]["min"],
                max_value=self.DEFAULT_PARAMETERS[p]["max"],
            )
            for p in TuningParameter
        }

    def get_accuracy_stats(self) -> dict[str, Any]:
        """Get recommendation accuracy statistics."""
        if self._recommendation_total_count == 0:
            return {
                "total_recommendations": 0,
                "successful": 0,
                "accuracy": 0.0,
                "target_accuracy": 0.8,
            }

        return {
            "total_recommendations": self._recommendation_total_count,
            "successful": self._recommendation_success_count,
            "accuracy": self._recommendation_success_count / self._recommendation_total_count,
            "target_accuracy": 0.8,
            "meets_target": (self._recommendation_success_count / self._recommendation_total_count) >= 0.8,
        }
