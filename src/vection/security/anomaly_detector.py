"""Anomaly Detector - Suspicious pattern detection.

Provides real-time anomaly detection for VECTION operations.
Monitors for suspicious patterns that may indicate abuse, attacks,
or system malfunction.

Features:
- Burst detection (rapid repeated operations)
- Velocity anomaly detection (abnormal trajectory changes)
- Pattern drift detection (unusual changes in signal patterns)
- Statistical outlier detection
- Configurable thresholds and sensitivity
- Alert generation with severity levels
- Integration with audit logging
- Thread-safe implementation

Usage:
    from vection.security.anomaly_detector import AnomalyDetector, AnomalyType

    detector = AnomalyDetector()

    # Check for anomalies in reinforcement pattern
    alert = detector.check_reinforcement_burst(session_id, signal_id, count=5, window_seconds=10)
    if alert:
        handle_anomaly(alert)

    # Register callback for real-time alerts
    detector.on_anomaly(lambda alert: send_to_siem(alert))
"""

from __future__ import annotations

import hashlib
import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AnomalyType(str, Enum):
    """Types of anomalies that can be detected."""

    # Reinforcement anomalies
    BURST_REINFORCEMENT = "burst_reinforcement"
    RAPID_CONFIDENCE_GAIN = "rapid_confidence_gain"
    SUSTAINED_REINFORCEMENT = "sustained_reinforcement"

    # Velocity anomalies
    VELOCITY_SPIKE = "velocity_spike"
    VELOCITY_REVERSAL = "velocity_reversal"
    MOMENTUM_ANOMALY = "momentum_anomaly"
    DRIFT_ANOMALY = "drift_anomaly"

    # Pattern anomalies
    PATTERN_DRIFT = "pattern_drift"
    PATTERN_HIJACK = "pattern_hijack"
    SIGNAL_FLOODING = "signal_flooding"

    # Session anomalies
    CROSS_SESSION_CORRELATION = "cross_session_correlation"
    SESSION_ENUMERATION = "session_enumeration"
    UNUSUAL_ACCESS_PATTERN = "unusual_access_pattern"

    # Statistical anomalies
    STATISTICAL_OUTLIER = "statistical_outlier"
    DISTRIBUTION_SHIFT = "distribution_shift"

    # System anomalies
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    TIMESTAMP_MANIPULATION = "timestamp_manipulation"

    # Generic
    CUSTOM = "custom"


class AlertSeverity(str, Enum):
    """Severity levels for anomaly alerts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Status of an anomaly alert."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


# Default severity mapping for anomaly types
DEFAULT_ALERT_SEVERITY: dict[AnomalyType, AlertSeverity] = {
    AnomalyType.BURST_REINFORCEMENT: AlertSeverity.MEDIUM,
    AnomalyType.RAPID_CONFIDENCE_GAIN: AlertSeverity.MEDIUM,
    AnomalyType.SUSTAINED_REINFORCEMENT: AlertSeverity.HIGH,
    AnomalyType.VELOCITY_SPIKE: AlertSeverity.LOW,
    AnomalyType.VELOCITY_REVERSAL: AlertSeverity.LOW,
    AnomalyType.MOMENTUM_ANOMALY: AlertSeverity.MEDIUM,
    AnomalyType.DRIFT_ANOMALY: AlertSeverity.MEDIUM,
    AnomalyType.PATTERN_DRIFT: AlertSeverity.MEDIUM,
    AnomalyType.PATTERN_HIJACK: AlertSeverity.HIGH,
    AnomalyType.SIGNAL_FLOODING: AlertSeverity.HIGH,
    AnomalyType.CROSS_SESSION_CORRELATION: AlertSeverity.HIGH,
    AnomalyType.SESSION_ENUMERATION: AlertSeverity.HIGH,
    AnomalyType.UNUSUAL_ACCESS_PATTERN: AlertSeverity.MEDIUM,
    AnomalyType.STATISTICAL_OUTLIER: AlertSeverity.LOW,
    AnomalyType.DISTRIBUTION_SHIFT: AlertSeverity.MEDIUM,
    AnomalyType.RESOURCE_EXHAUSTION: AlertSeverity.CRITICAL,
    AnomalyType.TIMESTAMP_MANIPULATION: AlertSeverity.HIGH,
    AnomalyType.CUSTOM: AlertSeverity.MEDIUM,
}


@dataclass
class AnomalyAlert:
    """An anomaly detection alert.

    Attributes:
        alert_id: Unique identifier for this alert.
        anomaly_type: Type of anomaly detected.
        severity: Alert severity level.
        status: Current alert status.
        session_id: Associated session (if any).
        description: Human-readable description.
        detected_at: When the anomaly was detected.
        metrics: Quantitative metrics about the anomaly.
        threshold: Threshold that was exceeded.
        actual_value: Actual value that triggered the alert.
        context: Additional context information.
        recommended_action: Suggested response action.
    """

    alert_id: str
    anomaly_type: AnomalyType
    severity: AlertSeverity
    status: AlertStatus
    session_id: str | None
    description: str
    detected_at: datetime
    metrics: dict[str, Any] = field(default_factory=dict)
    threshold: float | None = None
    actual_value: float | None = None
    context: dict[str, Any] = field(default_factory=dict)
    recommended_action: str = ""

    @property
    def age_seconds(self) -> float:
        """Get alert age in seconds."""
        return (datetime.now(UTC) - self.detected_at).total_seconds()

    def acknowledge(self) -> None:
        """Mark alert as acknowledged."""
        self.status = AlertStatus.ACKNOWLEDGED

    def resolve(self, false_positive: bool = False) -> None:
        """Mark alert as resolved.

        Args:
            false_positive: Whether this was a false positive.
        """
        if false_positive:
            self.status = AlertStatus.FALSE_POSITIVE
        else:
            self.status = AlertStatus.RESOLVED

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "alert_id": self.alert_id,
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity.value,
            "status": self.status.value,
            "session_id": self.session_id,
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
            "age_seconds": round(self.age_seconds, 1),
            "metrics": self.metrics,
            "threshold": self.threshold,
            "actual_value": self.actual_value,
            "context": self.context,
            "recommended_action": self.recommended_action,
        }


@dataclass
class DetectionThresholds:
    """Configurable thresholds for anomaly detection.

    Attributes:
        burst_count: Requests in window to trigger burst alert.
        burst_window_seconds: Window for burst detection.
        confidence_gain_rate: Max confidence gain per minute.
        velocity_spike_threshold: Max velocity change.
        drift_threshold: Max drift value.
        signal_flood_count: Signals per minute to trigger flood alert.
        statistical_zscore: Z-score for statistical outlier detection.
        pattern_drift_percent: Percent change for pattern drift.
    """

    burst_count: int = 10
    burst_window_seconds: float = 30.0
    confidence_gain_rate: float = 0.5
    velocity_spike_threshold: float = 0.8
    drift_threshold: float = 0.7
    signal_flood_count: int = 50
    statistical_zscore: float = 3.0
    pattern_drift_percent: float = 30.0
    sustained_reinforcement_count: int = 20
    sustained_reinforcement_window: float = 300.0


@dataclass
class AnomalyDetectorConfig:
    """Configuration for the anomaly detector.

    Attributes:
        thresholds: Detection thresholds.
        enable_logging: Whether to log detection events.
        max_alerts: Maximum alerts to retain.
        alert_cooldown_seconds: Minimum time between similar alerts.
        track_metrics_window: Window for metric tracking.
        sensitivity: Overall detection sensitivity (0.0 - 1.0).
    """

    thresholds: DetectionThresholds = field(default_factory=DetectionThresholds)
    enable_logging: bool = True
    max_alerts: int = 1000
    alert_cooldown_seconds: float = 60.0
    track_metrics_window: float = 3600.0
    sensitivity: float = 0.5


@dataclass
class MetricTimeSeries:
    """Time series data for a metric.

    Attributes:
        name: Metric name.
        values: Deque of (timestamp, value) pairs.
        max_size: Maximum values to retain.
    """

    name: str
    values: deque[tuple[float, float]] = field(default_factory=lambda: deque(maxlen=1000))
    max_size: int = 1000

    def add(self, value: float, timestamp: float | None = None) -> None:
        """Add a value to the time series.

        Args:
            value: Metric value.
            timestamp: Timestamp (defaults to now).
        """
        ts = timestamp or time.time()
        self.values.append((ts, value))

    def get_recent(self, window_seconds: float) -> list[float]:
        """Get values from recent time window.

        Args:
            window_seconds: Window size.

        Returns:
            List of recent values.
        """
        cutoff = time.time() - window_seconds
        return [v for ts, v in self.values if ts >= cutoff]

    def get_statistics(self, window_seconds: float | None = None) -> dict[str, float]:
        """Calculate statistics for the time series.

        Args:
            window_seconds: Window for calculation (None for all data).

        Returns:
            Dictionary with mean, std, min, max, count.
        """
        if window_seconds:
            values = self.get_recent(window_seconds)
        else:
            values = [v for _, v in self.values]

        if not values:
            return {"mean": 0, "std": 0, "min": 0, "max": 0, "count": 0}

        return {
            "mean": statistics.mean(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
            "count": len(values),
        }

    def get_zscore(self, value: float, window_seconds: float | None = None) -> float:
        """Calculate z-score for a value.

        Args:
            value: Value to check.
            window_seconds: Window for baseline calculation.

        Returns:
            Z-score (0 if insufficient data).
        """
        stats = self.get_statistics(window_seconds)
        if stats["std"] == 0 or stats["count"] < 3:
            return 0
        return (value - stats["mean"]) / stats["std"]


class AnomalyDetector:
    """Real-time anomaly detection for VECTION operations.

    Monitors for suspicious patterns and generates alerts when
    anomalies are detected. Integrates with audit logging for
    comprehensive security monitoring.

    Thread-safe and suitable for concurrent use.

    Usage:
        detector = AnomalyDetector()

        # Check for burst patterns
        alert = detector.check_reinforcement_burst("session_123", "signal_456")
        if alert:
            logger.warning(f"Anomaly detected: {alert.description}")

        # Register callback for all anomalies
        detector.on_anomaly(lambda alert: alert_system.send(alert))
    """

    def __init__(self, config: AnomalyDetectorConfig | None = None) -> None:
        """Initialize the anomaly detector.

        Args:
            config: Detector configuration.
        """
        self.config = config or AnomalyDetectorConfig()
        self._lock = threading.Lock()

        # Event tracking per session
        # Structure: {session_id: {event_type: [(timestamp, data)]}}
        self._event_history: dict[str, dict[str, deque[tuple[float, Any]]]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=1000))
        )

        # Metric time series per session
        # Structure: {session_id: {metric_name: MetricTimeSeries}}
        self._metrics: dict[str, dict[str, MetricTimeSeries]] = defaultdict(dict)

        # Alert storage
        self._alerts: deque[AnomalyAlert] = deque(maxlen=self.config.max_alerts)
        self._alert_cooldowns: dict[str, float] = {}  # {cooldown_key: last_alert_time}

        # Callbacks
        self._callbacks: list[Callable[[AnomalyAlert], None]] = []

        # Statistics
        self._total_checks = 0
        self._total_alerts = 0
        self._alerts_by_type: dict[AnomalyType, int] = defaultdict(int)

        # Audit logger (lazy loaded)
        self._audit_logger: Any = None

        logger.info(f"AnomalyDetector initialized with sensitivity: {self.config.sensitivity}")

    def check_reinforcement_burst(
        self,
        session_id: str,
        signal_id: str | None = None,
        count: int | None = None,
        window_seconds: float | None = None,
    ) -> AnomalyAlert | None:
        """Check for burst reinforcement patterns.

        Detects rapid, repeated reinforcement of signals which may
        indicate an attempt to artificially boost confidence.

        Args:
            session_id: Session identifier.
            signal_id: Optional specific signal being reinforced.
            count: Number of reinforcements (None to use tracked events).
            window_seconds: Time window (None for config default).

        Returns:
            AnomalyAlert if burst detected, None otherwise.
        """
        with self._lock:
            self._total_checks += 1
            window = window_seconds or self.config.thresholds.burst_window_seconds
            threshold = self._adjust_threshold(self.config.thresholds.burst_count)

            # Track the event
            event_key = f"reinforce:{signal_id}" if signal_id else "reinforce:*"
            self._track_event(session_id, event_key, {"signal_id": signal_id})

            # Count events in window
            if count is None:
                events = self._get_events_in_window(session_id, event_key, window)
                count = len(events)

            if count >= threshold:
                return self._create_alert(
                    anomaly_type=AnomalyType.BURST_REINFORCEMENT,
                    session_id=session_id,
                    description=f"Burst reinforcement detected: {count} reinforcements in {window}s",
                    threshold=threshold,
                    actual_value=count,
                    metrics={
                        "reinforcement_count": count,
                        "window_seconds": window,
                        "signal_id": signal_id,
                    },
                    recommended_action="Review session activity and consider rate limiting",
                )

            return None

    def check_confidence_gain(
        self,
        session_id: str,
        signal_id: str,
        previous_confidence: float,
        new_confidence: float,
        time_delta_seconds: float,
    ) -> AnomalyAlert | None:
        """Check for rapid confidence gain.

        Detects when signal confidence increases too quickly, which
        may indicate confidence manipulation.

        Args:
            session_id: Session identifier.
            signal_id: Signal being modified.
            previous_confidence: Previous confidence value.
            new_confidence: New confidence value.
            time_delta_seconds: Time between measurements.

        Returns:
            AnomalyAlert if anomaly detected, None otherwise.
        """
        with self._lock:
            self._total_checks += 1

            if time_delta_seconds <= 0:
                return None

            # Calculate gain rate (per minute)
            gain = new_confidence - previous_confidence
            gain_rate = (gain / time_delta_seconds) * 60

            # Track metric
            metric_key = f"confidence_gain:{signal_id}"
            self._track_metric(session_id, metric_key, gain_rate)

            threshold = self._adjust_threshold(self.config.thresholds.confidence_gain_rate)

            if gain_rate > threshold:
                return self._create_alert(
                    anomaly_type=AnomalyType.RAPID_CONFIDENCE_GAIN,
                    session_id=session_id,
                    description=f"Rapid confidence gain: {gain_rate:.2f}/min (threshold: {threshold:.2f})",
                    threshold=threshold,
                    actual_value=gain_rate,
                    metrics={
                        "signal_id": signal_id,
                        "previous_confidence": previous_confidence,
                        "new_confidence": new_confidence,
                        "gain_rate_per_minute": gain_rate,
                        "time_delta_seconds": time_delta_seconds,
                    },
                    recommended_action="Investigate signal reinforcement sources",
                )

            return None

    def check_velocity_anomaly(
        self,
        session_id: str,
        velocity_magnitude: float,
        velocity_direction: str,
        momentum: float,
        drift: float,
    ) -> AnomalyAlert | None:
        """Check for velocity anomalies.

        Detects abnormal changes in cognitive velocity that may
        indicate manipulation or unusual behavior.

        Args:
            session_id: Session identifier.
            velocity_magnitude: Current velocity magnitude.
            velocity_direction: Current direction.
            momentum: Current momentum.
            drift: Current drift value.

        Returns:
            AnomalyAlert if anomaly detected, None otherwise.
        """
        with self._lock:
            self._total_checks += 1

            # Track metrics
            self._track_metric(session_id, "velocity_magnitude", velocity_magnitude)
            self._track_metric(session_id, "momentum", momentum)
            self._track_metric(session_id, "drift", drift)

            alerts: list[AnomalyAlert] = []

            # Check for velocity spike
            magnitude_series = self._get_metric_series(session_id, "velocity_magnitude")
            if magnitude_series:
                zscore = magnitude_series.get_zscore(velocity_magnitude, window_seconds=300)
                spike_threshold = self._adjust_threshold(self.config.thresholds.statistical_zscore)

                if abs(zscore) > spike_threshold:
                    alert = self._create_alert(
                        anomaly_type=AnomalyType.VELOCITY_SPIKE,
                        session_id=session_id,
                        description=f"Velocity spike detected: z-score {zscore:.2f}",
                        threshold=spike_threshold,
                        actual_value=abs(zscore),
                        metrics={
                            "velocity_magnitude": velocity_magnitude,
                            "zscore": zscore,
                            "direction": velocity_direction,
                        },
                        recommended_action="Review session activity for unusual patterns",
                    )
                    if alert:
                        alerts.append(alert)

            # Check for excessive drift
            drift_threshold = self._adjust_threshold(self.config.thresholds.drift_threshold)
            if abs(drift) > drift_threshold:
                alert = self._create_alert(
                    anomaly_type=AnomalyType.DRIFT_ANOMALY,
                    session_id=session_id,
                    description=f"Excessive drift detected: {drift:.2f}",
                    threshold=drift_threshold,
                    actual_value=abs(drift),
                    metrics={
                        "drift": drift,
                        "direction": velocity_direction,
                        "momentum": momentum,
                    },
                    recommended_action="Session trajectory is unstable - monitor closely",
                )
                if alert:
                    alerts.append(alert)

            # Return first alert (most severe)
            return alerts[0] if alerts else None

    def check_signal_flood(
        self,
        session_id: str,
        signals_per_minute: int | None = None,
    ) -> AnomalyAlert | None:
        """Check for signal flooding.

        Detects when too many signals are being created, which may
        indicate an attempt to overwhelm the system.

        Args:
            session_id: Session identifier.
            signals_per_minute: Signal creation rate (None to calculate).

        Returns:
            AnomalyAlert if flooding detected, None otherwise.
        """
        with self._lock:
            self._total_checks += 1

            # Track signal creation
            self._track_event(session_id, "signal_create", {})

            # Calculate rate
            if signals_per_minute is None:
                events = self._get_events_in_window(session_id, "signal_create", 60.0)
                signals_per_minute = len(events)

            threshold = self._adjust_threshold(self.config.thresholds.signal_flood_count)

            if signals_per_minute >= threshold:
                return self._create_alert(
                    anomaly_type=AnomalyType.SIGNAL_FLOODING,
                    session_id=session_id,
                    description=f"Signal flooding detected: {signals_per_minute} signals/min",
                    threshold=threshold,
                    actual_value=signals_per_minute,
                    metrics={
                        "signals_per_minute": signals_per_minute,
                    },
                    recommended_action="Apply rate limiting to signal creation",
                )

            return None

    def check_timestamp_anomaly(
        self,
        session_id: str,
        timestamps: list[float],
    ) -> AnomalyAlert | None:
        """Check for timestamp manipulation.

        Detects non-monotonic or suspicious timestamp patterns that
        may indicate manipulation attempts.

        Args:
            session_id: Session identifier.
            timestamps: List of timestamps to check.

        Returns:
            AnomalyAlert if anomaly detected, None otherwise.
        """
        with self._lock:
            self._total_checks += 1

            if len(timestamps) < 2:
                return None

            # Check for non-monotonic timestamps
            non_monotonic_count = 0
            for i in range(1, len(timestamps)):
                if timestamps[i] < timestamps[i - 1]:
                    non_monotonic_count += 1

            if non_monotonic_count > 0:
                return self._create_alert(
                    anomaly_type=AnomalyType.TIMESTAMP_MANIPULATION,
                    session_id=session_id,
                    description=f"Non-monotonic timestamps detected: {non_monotonic_count} violations",
                    threshold=0,
                    actual_value=non_monotonic_count,
                    metrics={
                        "non_monotonic_count": non_monotonic_count,
                        "total_timestamps": len(timestamps),
                    },
                    recommended_action="Investigate timestamp source integrity",
                )

            return None

    def check_statistical_outlier(
        self,
        session_id: str,
        metric_name: str,
        value: float,
        window_seconds: float = 3600.0,
    ) -> AnomalyAlert | None:
        """Check if a value is a statistical outlier.

        Args:
            session_id: Session identifier.
            metric_name: Name of the metric.
            value: Value to check.
            window_seconds: Window for baseline calculation.

        Returns:
            AnomalyAlert if outlier detected, None otherwise.
        """
        with self._lock:
            self._total_checks += 1

            # Track metric
            self._track_metric(session_id, metric_name, value)

            # Get series and calculate z-score
            series = self._get_metric_series(session_id, metric_name)
            if series is None or len(series.values) < 10:
                return None

            zscore = series.get_zscore(value, window_seconds)
            threshold = self._adjust_threshold(self.config.thresholds.statistical_zscore)

            if abs(zscore) > threshold:
                stats = series.get_statistics(window_seconds)
                return self._create_alert(
                    anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                    session_id=session_id,
                    description=f"Statistical outlier in {metric_name}: z-score {zscore:.2f}",
                    threshold=threshold,
                    actual_value=abs(zscore),
                    metrics={
                        "metric_name": metric_name,
                        "value": value,
                        "zscore": zscore,
                        "baseline_mean": stats["mean"],
                        "baseline_std": stats["std"],
                    },
                    recommended_action="Review metric source for anomalies",
                )

            return None

    def check_custom(
        self,
        session_id: str,
        condition: bool,
        anomaly_type: AnomalyType = AnomalyType.CUSTOM,
        description: str = "Custom anomaly detected",
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        metrics: dict[str, Any] | None = None,
        recommended_action: str = "",
    ) -> AnomalyAlert | None:
        """Create a custom anomaly alert if condition is met.

        Args:
            session_id: Session identifier.
            condition: Whether anomaly condition is met.
            anomaly_type: Type of anomaly.
            description: Alert description.
            severity: Alert severity.
            metrics: Additional metrics.
            recommended_action: Suggested action.

        Returns:
            AnomalyAlert if condition is True, None otherwise.
        """
        with self._lock:
            self._total_checks += 1

            if condition:
                return self._create_alert(
                    anomaly_type=anomaly_type,
                    session_id=session_id,
                    description=description,
                    severity_override=severity,
                    metrics=metrics or {},
                    recommended_action=recommended_action,
                )

            return None

    def on_anomaly(self, callback: Callable[[AnomalyAlert], None]) -> None:
        """Register a callback for anomaly alerts.

        Args:
            callback: Function called with each new alert.
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[AnomalyAlert], None]) -> None:
        """Remove a callback.

        Args:
            callback: Callback to remove.
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_alerts(
        self,
        session_id: str | None = None,
        anomaly_type: AnomalyType | None = None,
        severity: AlertSeverity | None = None,
        status: AlertStatus | None = None,
        limit: int = 100,
    ) -> list[AnomalyAlert]:
        """Get alerts with optional filtering.

        Args:
            session_id: Filter by session.
            anomaly_type: Filter by type.
            severity: Filter by severity.
            status: Filter by status.
            limit: Maximum alerts to return.

        Returns:
            List of matching alerts.
        """
        with self._lock:
            alerts = list(self._alerts)

            if session_id is not None:
                alerts = [a for a in alerts if a.session_id == session_id]

            if anomaly_type is not None:
                alerts = [a for a in alerts if a.anomaly_type == anomaly_type]

            if severity is not None:
                alerts = [a for a in alerts if a.severity == severity]

            if status is not None:
                alerts = [a for a in alerts if a.status == status]

            return alerts[-limit:]

    def get_active_alerts(self, session_id: str | None = None) -> list[AnomalyAlert]:
        """Get active (unresolved) alerts.

        Args:
            session_id: Optional session filter.

        Returns:
            List of active alerts.
        """
        return self.get_alerts(session_id=session_id, status=AlertStatus.ACTIVE)

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert.

        Args:
            alert_id: Alert to acknowledge.

        Returns:
            True if alert was found and acknowledged.
        """
        with self._lock:
            for alert in self._alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledge()
                    return True
            return False

    def resolve_alert(self, alert_id: str, false_positive: bool = False) -> bool:
        """Resolve an alert.

        Args:
            alert_id: Alert to resolve.
            false_positive: Whether this was a false positive.

        Returns:
            True if alert was found and resolved.
        """
        with self._lock:
            for alert in self._alerts:
                if alert.alert_id == alert_id:
                    alert.resolve(false_positive)
                    return True
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get detector statistics.

        Returns:
            Dictionary with statistics.
        """
        with self._lock:
            active_alerts = len([a for a in self._alerts if a.status == AlertStatus.ACTIVE])

            return {
                "total_checks": self._total_checks,
                "total_alerts": self._total_alerts,
                "active_alerts": active_alerts,
                "alert_rate_percent": (
                    round((self._total_alerts / self._total_checks) * 100, 4) if self._total_checks > 0 else 0
                ),
                "alerts_by_type": dict(self._alerts_by_type),
                "tracked_sessions": len(self._event_history),
                "sensitivity": self.config.sensitivity,
                "callbacks_registered": len(self._callbacks),
            }

    def clear_session_data(self, session_id: str) -> None:
        """Clear all tracked data for a session.

        Args:
            session_id: Session to clear.
        """
        with self._lock:
            if session_id in self._event_history:
                del self._event_history[session_id]
            if session_id in self._metrics:
                del self._metrics[session_id]

    def _track_event(self, session_id: str, event_type: str, data: Any) -> None:
        """Track an event for anomaly detection.

        Args:
            session_id: Session identifier.
            event_type: Type of event.
            data: Event data.
        """
        self._event_history[session_id][event_type].append((time.time(), data))

    def _get_events_in_window(
        self,
        session_id: str,
        event_type: str,
        window_seconds: float,
    ) -> list[tuple[float, Any]]:
        """Get events within a time window.

        Args:
            session_id: Session identifier.
            event_type: Type of event.
            window_seconds: Window size.

        Returns:
            List of (timestamp, data) tuples.
        """
        cutoff = time.time() - window_seconds
        events = self._event_history[session_id][event_type]
        return [(ts, data) for ts, data in events if ts >= cutoff]

    def _track_metric(self, session_id: str, metric_name: str, value: float) -> None:
        """Track a metric value.

        Args:
            session_id: Session identifier.
            metric_name: Metric name.
            value: Metric value.
        """
        if metric_name not in self._metrics[session_id]:
            self._metrics[session_id][metric_name] = MetricTimeSeries(name=metric_name)
        self._metrics[session_id][metric_name].add(value)

    def _get_metric_series(self, session_id: str, metric_name: str) -> MetricTimeSeries | None:
        """Get metric time series.

        Args:
            session_id: Session identifier.
            metric_name: Metric name.

        Returns:
            MetricTimeSeries or None.
        """
        return self._metrics.get(session_id, {}).get(metric_name)

    def _adjust_threshold(self, base_threshold: float) -> float:
        """Adjust threshold based on sensitivity.

        Args:
            base_threshold: Base threshold value.

        Returns:
            Adjusted threshold.
        """
        # Higher sensitivity = lower thresholds (more alerts)
        # Lower sensitivity = higher thresholds (fewer alerts)
        sensitivity_factor = 2.0 - self.config.sensitivity  # 1.5 at 0.5 sensitivity
        return base_threshold * sensitivity_factor

    def _create_alert(
        self,
        anomaly_type: AnomalyType,
        session_id: str | None,
        description: str,
        threshold: float | None = None,
        actual_value: float | None = None,
        metrics: dict[str, Any] | None = None,
        recommended_action: str = "",
        severity_override: AlertSeverity | None = None,
    ) -> AnomalyAlert | None:
        """Create an anomaly alert if not in cooldown.

        Args:
            anomaly_type: Type of anomaly.
            session_id: Session identifier.
            description: Alert description.
            threshold: Threshold that was exceeded.
            actual_value: Actual value.
            metrics: Additional metrics.
            recommended_action: Suggested action.
            severity_override: Override default severity.

        Returns:
            AnomalyAlert or None if in cooldown.
        """
        # Check cooldown
        cooldown_key = f"{session_id}:{anomaly_type.value}"
        now = time.time()

        if cooldown_key in self._alert_cooldowns:
            last_alert = self._alert_cooldowns[cooldown_key]
            if now - last_alert < self.config.alert_cooldown_seconds:
                return None

        # Generate alert ID
        alert_id = self._generate_alert_id(anomaly_type, session_id)

        # Determine severity
        severity = severity_override or DEFAULT_ALERT_SEVERITY.get(anomaly_type, AlertSeverity.MEDIUM)

        # Create alert
        alert = AnomalyAlert(
            alert_id=alert_id,
            anomaly_type=anomaly_type,
            severity=severity,
            status=AlertStatus.ACTIVE,
            session_id=session_id,
            description=description,
            detected_at=datetime.now(UTC),
            threshold=threshold,
            actual_value=actual_value,
            metrics=metrics or {},
            recommended_action=recommended_action,
        )

        # Store alert
        self._alerts.append(alert)
        self._alert_cooldowns[cooldown_key] = now
        self._total_alerts += 1
        self._alerts_by_type[anomaly_type] += 1

        # Log to audit logger
        if self.config.enable_logging:
            self._log_alert(alert)

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.warning(f"Anomaly callback error: {e}")

        logger.warning(f"Anomaly detected: {anomaly_type.value} - {description}")

        return alert

    def _generate_alert_id(self, anomaly_type: AnomalyType, session_id: str | None) -> str:
        """Generate a unique alert ID."""
        timestamp = int(time.time() * 1000000)
        hash_input = f"{anomaly_type.value}:{session_id}:{timestamp}"
        return f"alert_{hashlib.sha256(hash_input.encode()).hexdigest()[:12]}"

    def _log_alert(self, alert: AnomalyAlert) -> None:
        """Log alert to audit logger."""
        try:
            if self._audit_logger is None:
                from vection.security.audit_logger import get_audit_logger

                self._audit_logger = get_audit_logger()

            self._audit_logger.log_anomaly(
                anomaly_type=alert.anomaly_type.value,
                session_id=alert.session_id or "unknown",
                description=alert.description,
                metrics=alert.metrics,
            )
        except Exception:
            pass


# Module-level singleton
_anomaly_detector: AnomalyDetector | None = None


def get_anomaly_detector(config: AnomalyDetectorConfig | None = None) -> AnomalyDetector:
    """Get the global anomaly detector instance.

    Args:
        config: Configuration (only used on first call).

    Returns:
        AnomalyDetector singleton.
    """
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = AnomalyDetector(config)
    return _anomaly_detector
