"""
Statistical Anomaly Detection for Parasite Guard.

Implements adaptive threshold anomaly detection using:
- Rolling Z-score analysis
- Adaptive thresholds based on 99th percentile
- Multi-dimensional anomaly detection (optional, requires sklearn)

Provides real-time detection of parasitic patterns based on statistical analysis.
"""

from __future__ import annotations

import logging
import math
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    """Result of anomaly detection.

    Attributes:
        is_anomaly: Whether an anomaly was detected.
        z_score: The Z-score of the value.
        confidence: Statistical confidence level (0.0 to 1.0).
        threshold: The threshold used for detection.
        baseline_mean: Mean of the baseline window.
        baseline_std: Standard deviation of the baseline window.
        value: The value that was analyzed.
        timestamp: When the detection occurred.
    """

    is_anomaly: bool
    z_score: float
    confidence: float
    threshold: float
    baseline_mean: float
    baseline_std: float
    value: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "is_anomaly": self.is_anomaly,
            "z_score": self.z_score,
            "confidence": self.confidence,
            "threshold": self.threshold,
            "baseline_mean": self.baseline_mean,
            "baseline_std": self.baseline_std,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class BaselineMetrics:
    """Baseline statistics for anomaly detection.

    Attributes:
        mean: Mean of the baseline data.
        std: Standard deviation.
        min_value: Minimum value observed.
        max_value: Maximum value observed.
        sample_size: Number of samples in the baseline.
        anomaly_rate: Rate of anomalies detected.
    """

    mean: float = 0.0
    std: float = 1.0
    min_value: float = 0.0
    max_value: float = 0.0
    sample_size: int = 0
    anomaly_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "mean": self.mean,
            "std": self.std,
            "min": self.min_value,
            "max": self.max_value,
            "sample_size": self.sample_size,
            "anomaly_rate": self.anomaly_rate,
        }


class AdaptiveAnomalyDetector:
    """Time-series anomaly detection with rolling Z-scores and adaptive thresholds.

    Uses a sliding window to calculate baseline statistics and detects anomalies
    when values deviate significantly from the baseline. The threshold is adaptive,
    adjusting based on the 99th percentile of observed Z-scores.

    This implementation does not require any external dependencies (numpy, scipy)
    and uses pure Python for calculations.

    Attributes:
        window_size: Size of the sliding window for baseline calculation.
        z_threshold: Maximum Z-score threshold (configurable default).
        adaptive_percentile: Percentile for adaptive threshold calculation.
    """

    def __init__(
        self,
        window_size: int = 60,
        z_threshold: float = 3.5,
        adaptive_percentile: float = 99.0,
        component: str = "unknown",
    ):
        """Initialize the anomaly detector.

        Args:
            window_size: Number of samples to use for baseline calculation.
            z_threshold: Default Z-score threshold for anomaly detection.
            adaptive_percentile: Percentile for adaptive threshold (e.g., 99.0).
            component: Component name for metrics.
        """
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.adaptive_percentile = adaptive_percentile
        self.component = component

        self._history: deque[float] = deque(maxlen=window_size * 2)
        self._z_score_history: deque[float] = deque(maxlen=window_size)
        self._anomaly_count = 0
        self._total_count = 0

    def _calculate_mean(self, values: list[float]) -> float:
        """Calculate mean of values."""
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _calculate_std(self, values: list[float], mean: float) -> float:
        """Calculate standard deviation of values."""
        if len(values) < 2:
            return 1.0
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance) if variance > 0 else 1e-9

    def _calculate_percentile(self, values: list[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * (percentile / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_values[int(k)]
        d0 = sorted_values[int(f)] * (c - k)
        d1 = sorted_values[int(c)] * (k - f)
        return d0 + d1

    def _normal_cdf(self, x: float) -> float:
        """Approximate normal CDF using error function approximation."""
        # Approximation of the standard normal CDF
        # Using Horner's method for the polynomial approximation
        t = 1.0 / (1.0 + 0.2316419 * abs(x))
        d = 0.3989422804014327  # 1/sqrt(2*pi)
        poly = (
            t
            * (
                0.319381530
                + t
                * (
                    -0.356563782
                    + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))
                )
            )
        )
        cdf = 1.0 - d * math.exp(-0.5 * x * x) * poly
        return cdf if x >= 0 else 1.0 - cdf

    def detect(self, value: float) -> AnomalyResult:
        """Detect if a value is anomalous.

        Args:
            value: The value to analyze.

        Returns:
            AnomalyResult with detection details.
        """
        self._total_count += 1
        self._history.append(value)

        # Not enough data for detection
        if len(self._history) < self.window_size:
            return AnomalyResult(
                is_anomaly=False,
                z_score=0.0,
                confidence=0.0,
                threshold=self.z_threshold,
                baseline_mean=0.0,
                baseline_std=1.0,
                value=value,
            )

        # Calculate baseline from window
        window = list(self._history)[-self.window_size :]
        mean = self._calculate_mean(window)
        std = self._calculate_std(window, mean)

        # Avoid division by zero
        if std < 1e-9:
            std = 1e-9

        # Calculate Z-score
        z_score = abs((value - mean) / std)
        self._z_score_history.append(z_score)

        # Calculate adaptive threshold based on recent Z-scores
        if len(self._z_score_history) >= 10:
            z_scores_list = list(self._z_score_history)
            adaptive_threshold = min(
                self._calculate_percentile(z_scores_list, self.adaptive_percentile),
                self.z_threshold,
            )
        else:
            adaptive_threshold = self.z_threshold

        # Determine if anomaly
        is_anomaly = z_score > adaptive_threshold

        if is_anomaly:
            self._anomaly_count += 1

        # Calculate confidence using CDF
        # Confidence = P(X < z_score) for normal distribution
        confidence = self._normal_cdf(z_score)

        result = AnomalyResult(
            is_anomaly=is_anomaly,
            z_score=z_score,
            confidence=confidence,
            threshold=adaptive_threshold,
            baseline_mean=mean,
            baseline_std=std,
            value=value,
        )

        # Emit metrics
        self._emit_metrics(result)

        return result

    def _emit_metrics(self, result: AnomalyResult) -> None:
        """Emit Prometheus metrics for the detection."""
        try:
            from .metrics import record_anomaly

            if result.is_anomaly:
                severity = "high" if result.z_score > 4.0 else "medium"
                record_anomaly(
                    component=self.component,
                    z_score=result.z_score,
                    severity=severity,
                    threshold=result.threshold,
                )
        except ImportError:
            pass  # Metrics not available

    def get_baseline_metrics(self) -> BaselineMetrics:
        """Get current baseline statistics.

        Returns:
            BaselineMetrics with current baseline information.
        """
        if len(self._history) < 2:
            return BaselineMetrics()

        values = list(self._history)
        mean = self._calculate_mean(values)
        std = self._calculate_std(values, mean)

        return BaselineMetrics(
            mean=mean,
            std=std,
            min_value=min(values),
            max_value=max(values),
            sample_size=len(values),
            anomaly_rate=(
                self._anomaly_count / self._total_count if self._total_count > 0 else 0.0
            ),
        )

    def reset(self) -> None:
        """Reset the detector state."""
        self._history.clear()
        self._z_score_history.clear()
        self._anomaly_count = 0
        self._total_count = 0
        logger.info(f"Anomaly detector reset for component: {self.component}")


class MultiWindowAnomalyDetector:
    """Multi-window anomaly detector for different time scales.

    Combines short-term and long-term windows to detect both
    sudden spikes and gradual drifts.
    """

    def __init__(
        self,
        short_window: int = 10,
        medium_window: int = 60,
        long_window: int = 300,
        z_threshold: float = 3.5,
        component: str = "unknown",
    ):
        """Initialize multi-window detector.

        Args:
            short_window: Short-term window size (seconds).
            medium_window: Medium-term window size.
            long_window: Long-term window size.
            z_threshold: Z-score threshold.
            component: Component name for metrics.
        """
        self.component = component
        self.short_detector = AdaptiveAnomalyDetector(
            window_size=short_window,
            z_threshold=z_threshold,
            component=f"{component}_short",
        )
        self.medium_detector = AdaptiveAnomalyDetector(
            window_size=medium_window,
            z_threshold=z_threshold,
            component=f"{component}_medium",
        )
        self.long_detector = AdaptiveAnomalyDetector(
            window_size=long_window,
            z_threshold=z_threshold,
            component=f"{component}_long",
        )

    def detect(self, value: float) -> dict[str, AnomalyResult]:
        """Detect anomalies across all windows.

        Args:
            value: The value to analyze.

        Returns:
            Dictionary with results from each window.
        """
        return {
            "short": self.short_detector.detect(value),
            "medium": self.medium_detector.detect(value),
            "long": self.long_detector.detect(value),
        }

    def is_anomaly(self, value: float, require_all: bool = False) -> bool:
        """Check if value is anomalous.

        Args:
            value: The value to analyze.
            require_all: If True, all windows must detect anomaly.
                        If False, any window detecting anomaly is enough.

        Returns:
            True if anomaly is detected.
        """
        results = self.detect(value)

        if require_all:
            return all(r.is_anomaly for r in results.values())
        return any(r.is_anomaly for r in results.values())

    def get_baseline_metrics(self) -> dict[str, BaselineMetrics]:
        """Get baseline metrics from all windows."""
        return {
            "short": self.short_detector.get_baseline_metrics(),
            "medium": self.medium_detector.get_baseline_metrics(),
            "long": self.long_detector.get_baseline_metrics(),
        }

    def reset(self) -> None:
        """Reset all detectors."""
        self.short_detector.reset()
        self.medium_detector.reset()
        self.long_detector.reset()


class RateLimitAnomalyDetector:
    """Detects anomalous request rates.

    Specialized for detecting parasitic patterns like:
    - Request floods
    - Sudden traffic spikes
    - Unusual patterns of activity
    """

    def __init__(
        self,
        window_seconds: float = 60.0,
        max_rate: float = 100.0,
        z_threshold: float = 3.0,
        component: str = "rate_limit",
    ):
        """Initialize rate limit detector.

        Args:
            window_seconds: Time window for rate calculation.
            max_rate: Maximum allowed rate (requests per second).
            z_threshold: Z-score threshold for rate anomalies.
            component: Component name for metrics.
        """
        self.window_seconds = window_seconds
        self.max_rate = max_rate
        self.component = component

        self._request_times: deque[float] = deque()
        self._rate_detector = AdaptiveAnomalyDetector(
            window_size=int(window_seconds),
            z_threshold=z_threshold,
            component=component,
        )

    def record_request(self) -> AnomalyResult:
        """Record a request and check for rate anomalies.

        Returns:
            AnomalyResult indicating if rate is anomalous.
        """
        now = datetime.now(timezone.utc).timestamp()
        self._request_times.append(now)

        # Remove old requests
        cutoff = now - self.window_seconds
        while self._request_times and self._request_times[0] < cutoff:
            self._request_times.popleft()

        # Calculate current rate
        current_rate = len(self._request_times) / self.window_seconds

        # Check against max rate
        if current_rate > self.max_rate:
            return AnomalyResult(
                is_anomaly=True,
                z_score=current_rate / self.max_rate,
                confidence=0.99,
                threshold=self.max_rate,
                baseline_mean=self.max_rate,
                baseline_std=self.max_rate * 0.1,
                value=current_rate,
            )

        # Check for statistical anomaly
        return self._rate_detector.detect(current_rate)

    def get_current_rate(self) -> float:
        """Get the current request rate."""
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - self.window_seconds

        # Count requests in window
        count = sum(1 for t in self._request_times if t >= cutoff)
        return count / self.window_seconds

    def reset(self) -> None:
        """Reset the detector."""
        self._request_times.clear()
        self._rate_detector.reset()
