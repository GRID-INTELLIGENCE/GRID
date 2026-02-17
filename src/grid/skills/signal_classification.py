"""Signal classification using audio engineering principles.

Classifies execution data as signal (valid, preserve) or noise (filter).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .execution_tracker import SkillExecutionRecord
    from .intelligence_tracker import IntelligenceRecord

logger = logging.getLogger(__name__)


class SignalType(StrEnum):
    """Types of valid signals in GRID Skills."""

    VALID_EXECUTION = "valid_execution"
    GENUINE_REGRESSION = "genuine_regression"
    INTELLIGENCE_PATTERN = "intelligence_pattern"
    STABLE_BASELINE = "stable_baseline"


class NoiseType(StrEnum):
    """Types of noise to filter out."""

    TRANSIENT_ERROR = "transient_error"
    FALSE_POSITIVE_REGRESSION = "false_positive"
    TIMEOUT_SPIKE = "timeout_spike"
    LOW_CONFIDENCE_OUTLIER = "low_confidence"
    NETWORK_JITTER = "network_jitter"
    SUSPICIOUSLY_FAST = "suspiciously_fast"


@dataclass
class ClassificationResult:
    """Result of signal/noise classification."""

    signal_type: str
    is_noise: bool
    confidence: float
    nsr_contribution: float
    action: str  # "preserve", "filter", "alert"
    reason: str


class NSRTracker:
    """Tracks Noise-to-Signal Ratio over time.

    Maintains running counts of signal vs noise classifications
    and provides breakdown by noise type.
    """

    def __init__(self):
        self._signal_count: int = 0
        self._noise_count: int = 0
        self._noise_breakdown: dict[str, int] = {}

    def record_classification(self, result: ClassificationResult) -> None:
        """Record a classification result."""
        if result.is_noise:
            self._noise_count += 1
            noise_type = result.signal_type
            self._noise_breakdown[noise_type] = self._noise_breakdown.get(noise_type, 0) + 1
        else:
            self._signal_count += 1

    def get_current_nsr(self) -> float:
        """Get current noise-to-signal ratio (0.0 to 1.0)."""
        total = self._signal_count + self._noise_count
        if total == 0:
            return 0.0
        return self._noise_count / total

    def get_noise_breakdown(self) -> dict[str, int]:
        """Get breakdown of noise by type."""
        return self._noise_breakdown.copy()

    def reset(self) -> None:
        """Reset all counters."""
        self._signal_count = 0
        self._noise_count = 0
        self._noise_breakdown.clear()


class SignalClassifier:
    """Audio engineering-inspired signal classifier.

    Configuration:
    - GRID_SKILLS_NSR_THRESHOLD: Initial NSR threshold (default: 0.10)
    - GRID_SKILLS_REGRESSION_THRESHOLD: Regression threshold (default: 1.2)
    """

    # Confirmed parameters
    NSR_INITIAL_THRESHOLD = float(os.getenv("GRID_SKILLS_NSR_THRESHOLD", "0.10"))
    NSR_TARGET_THRESHOLD = 0.05  # Tighten after stability proven
    REGRESSION_THRESHOLD = float(os.getenv("GRID_SKILLS_REGRESSION_THRESHOLD", "1.2"))

    # Mixing weights (audio engineering analogy)
    CONFIDENCE_WEIGHT = 0.7
    PERFORMANCE_WEIGHT = 0.3

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def classify(
        self,
        record: SkillExecutionRecord,
        baseline: dict[str, float] | None = None,
    ) -> ClassificationResult:
        """Classify execution as signal or noise.

        Args:
            record: Execution record to classify
            baseline: Performance baseline metrics

        Returns:
            ClassificationResult with signal type and action
        """
        hard_noise, soft_noise = self._detect_noise_indicators(record, baseline)

        if hard_noise:
            primary_noise = hard_noise[0]
            return ClassificationResult(
                signal_type=primary_noise.value,
                is_noise=True,
                confidence=max(0.0, 1.0 - (len(hard_noise) * 0.2)),
                nsr_contribution=min(len(hard_noise) * 0.1, 1.0),
                action="filter",
                reason=f"Noise detected: {', '.join(n.value for n in hard_noise)}",
            )

        if soft_noise:
            return ClassificationResult(
                signal_type=SignalType.VALID_EXECUTION.value,
                is_noise=False,
                confidence=0.7,
                nsr_contribution=0.0,
                action="monitor",
                reason=f"Soft noise indicators: {', '.join(n.value for n in soft_noise)}",
            )

        is_regression = self._is_genuine_regression(record, baseline)

        if is_regression:
            return ClassificationResult(
                signal_type=SignalType.GENUINE_REGRESSION.value,
                is_noise=False,
                confidence=0.85,
                nsr_contribution=0.0,
                action="alert",
                reason=f"Regression: {record.execution_time_ms:.0f}ms vs baseline",
            )

        return ClassificationResult(
            signal_type=SignalType.VALID_EXECUTION.value,
            is_noise=False,
            confidence=0.95,
            nsr_contribution=0.0,
            action="preserve",
            reason="Valid execution",
        )

    def classify_intelligence(self, record: IntelligenceRecord) -> ClassificationResult:
        """Classify intelligence decisions as signal or noise."""
        noise_indicators: list[NoiseType] = []

        if record.confidence < 0.1:
            noise_indicators.append(NoiseType.LOW_CONFIDENCE_OUTLIER)

        if record.outcome and record.outcome.lower() != "success":
            noise_indicators.append(NoiseType.TRANSIENT_ERROR)

        if noise_indicators:
            primary_noise = noise_indicators[0]
            return ClassificationResult(
                signal_type=primary_noise.value,
                is_noise=True,
                confidence=max(0.0, 1.0 - (len(noise_indicators) * 0.2)),
                nsr_contribution=min(len(noise_indicators) * 0.1, 1.0),
                action="filter",
                reason=f"Noise detected: {', '.join(n.value for n in noise_indicators)}",
            )

        return ClassificationResult(
            signal_type=SignalType.INTELLIGENCE_PATTERN.value,
            is_noise=False,
            confidence=min(max(record.confidence, 0.0), 1.0),
            nsr_contribution=0.0,
            action="preserve",
            reason="Intelligence decision",
        )

    def _detect_noise_indicators(
        self,
        record: SkillExecutionRecord,
        baseline: dict[str, float] | None,
    ) -> tuple[list[NoiseType], list[NoiseType]]:
        """Detect noise indicators in execution."""
        hard: list[NoiseType] = []
        soft: list[NoiseType] = []

        if record.error:
            error_lower = record.error.lower()
            if any(kw in error_lower for kw in ["timeout", "connection", "network"]):
                hard.append(NoiseType.TRANSIENT_ERROR)
            if "jitter" in error_lower:
                soft.append(NoiseType.NETWORK_JITTER)

        if record.confidence_score is not None and record.confidence_score < 0.1:
            hard.append(NoiseType.LOW_CONFIDENCE_OUTLIER)

        if record.execution_time_ms > 60000:
            hard.append(NoiseType.TIMEOUT_SPIKE)

        if record.execution_time_ms < 1:
            hard.append(NoiseType.SUSPICIOUSLY_FAST)

        if baseline and baseline.get("p50_ms", 0) > 0:
            baseline_p50 = baseline["p50_ms"]
            if baseline_p50 * 1.05 < record.execution_time_ms <= baseline_p50 * self.REGRESSION_THRESHOLD:
                soft.append(NoiseType.FALSE_POSITIVE_REGRESSION)

        return hard, soft

    def _is_genuine_regression(self, record: SkillExecutionRecord, baseline: dict[str, float] | None) -> bool:
        """Determine if execution shows genuine regression."""
        if not baseline or "p50_ms" not in baseline:
            return False

        baseline_p50 = baseline["p50_ms"]
        if baseline_p50 <= 0:
            return False

        return record.execution_time_ms > (baseline_p50 * self.REGRESSION_THRESHOLD)
