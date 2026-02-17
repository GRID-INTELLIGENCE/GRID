"""
Parasite Guard Prometheus Metrics.

Defines all Prometheus metrics for the Parasite Guard system:
- Detection metrics (latency, counts, precision)
- State transition metrics
- Threat distribution metrics
- Anomaly detection metrics
- Chaos engineering metrics
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Try to import prometheus_client, fallback to stubs if not available
try:
    from prometheus_client import REGISTRY, Counter, Gauge, Histogram

    def _get_or_create_counter(name: str, documentation: str, labelnames: list[str] | None = None) -> Counter:
        """Get existing counter or create new one."""
        if name in REGISTRY._names_to_collectors:
            return REGISTRY._names_to_collectors[name]
        return Counter(name, documentation, labelnames=labelnames or [])

    def _get_or_create_gauge(name: str, documentation: str, labelnames: list[str] | None = None) -> Gauge:
        """Get existing gauge or create new one."""
        if name in REGISTRY._names_to_collectors:
            return REGISTRY._names_to_collectors[name]
        return Gauge(name, documentation, labelnames=labelnames or [])

    def _get_or_create_histogram(
        name: str,
        documentation: str,
        labelnames: list[str] | None = None,
        buckets: list[float] | None = None,
    ) -> Histogram:
        """Get existing histogram or create new one."""
        if name in REGISTRY._names_to_collectors:
            return REGISTRY._names_to_collectors[name]
        return Histogram(
            name,
            documentation,
            labelnames=labelnames or [],
            buckets=buckets or Histogram.DEFAULT_BUCKETS,
        )

    METRICS_ENABLED = True

except ImportError:
    logger.warning("prometheus_client not available, metrics disabled")
    METRICS_ENABLED = False

    # Stub classes for when prometheus is not available
    class _StubMetric:
        def labels(self, *args: Any, **kwargs: Any) -> _StubMetric:
            return self

        def inc(self, amount: float = 1) -> None:
            pass

        def dec(self, amount: float = 1) -> None:
            pass

        def set(self, value: float) -> None:
            pass

        def observe(self, value: float) -> None:
            pass

    def _get_or_create_counter(*args: Any, **kwargs: Any) -> _StubMetric:
        return _StubMetric()

    def _get_or_create_gauge(*args: Any, **kwargs: Any) -> _StubMetric:
        return _StubMetric()

    def _get_or_create_histogram(*args: Any, **kwargs: Any) -> _StubMetric:
        return _StubMetric()


# =============================================================================
# Threat Detection Metrics
# =============================================================================

# Total parasites detected (for Pie Chart visualization)
parasite_detected_total = _get_or_create_counter(
    "parasite_detected_total",
    "Total parasites detected",
    labelnames=["component", "pattern", "severity"],
)

# Detection latency (target: <100ms)
detection_duration_seconds = _get_or_create_histogram(
    "parasite_detection_duration_seconds",
    "Time to detect parasites",
    labelnames=["detector"],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 1.0],
)

# Currently active parasites
active_parasites = _get_or_create_gauge(
    "parasite_active",
    "Currently active (unresolved) parasites",
    labelnames=["component"],
)

# False positive rate gauge
detection_false_positive_rate = _get_or_create_gauge(
    "parasite_detection_false_positive_rate",
    "Detection false positive rate",
    labelnames=["detector"],
)


# =============================================================================
# State Machine Metrics
# =============================================================================

# State transitions (for State Diagram visualization)
guard_state_transitions_total = _get_or_create_counter(
    "parasite_guard_state_transitions_total",
    "State machine transitions",
    labelnames=["from_state", "to_state", "confidence_bucket"],
)

# Current state gauge
guard_current_state = _get_or_create_gauge(
    "parasite_guard_current_state",
    "Current state of the guard (1=active, 0=inactive)",
    labelnames=["state"],
)

# Time spent in each state
guard_state_duration_seconds = _get_or_create_histogram(
    "parasite_guard_state_duration_seconds",
    "Time spent in each state before transitioning",
    labelnames=["state"],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
)


# =============================================================================
# Precision Metrics
# =============================================================================

# Precision (TP / (TP + FP))
detection_precision = _get_or_create_gauge(
    "parasite_detection_precision",
    "Detection precision (TP / (TP + FP))",
    labelnames=["detector"],
)

# Recall (TP / (TP + FN))
detection_recall = _get_or_create_gauge(
    "parasite_detection_recall",
    "Detection recall (TP / (TP + FN))",
    labelnames=["detector"],
)

# F1 Score
detection_f1_score = _get_or_create_gauge(
    "parasite_detection_f1_score",
    "Detection F1 score",
    labelnames=["detector"],
)


# =============================================================================
# Anomaly Detection Metrics
# =============================================================================

# Z-scores from anomaly detection
anomaly_z_score = _get_or_create_histogram(
    "parasite_anomaly_z_score",
    "Z-scores from anomaly detection",
    labelnames=["component"],
    buckets=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0],
)

# Adaptive threshold value
anomaly_threshold = _get_or_create_gauge(
    "parasite_anomaly_threshold",
    "Current adaptive anomaly threshold",
    labelnames=["component"],
)

# Anomalies detected
anomaly_detected_total = _get_or_create_counter(
    "parasite_anomaly_detected_total",
    "Total anomalies detected",
    labelnames=["component", "severity"],
)


# =============================================================================
# Sanitization Metrics
# =============================================================================

# Sanitization attempts
sanitization_attempts_total = _get_or_create_counter(
    "parasite_sanitization_attempts_total",
    "Total sanitization attempts",
    labelnames=["component", "success"],
)

# Sanitization duration
sanitization_duration_seconds = _get_or_create_histogram(
    "parasite_sanitization_duration_seconds",
    "Time to sanitize parasites",
    labelnames=["component"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)


# =============================================================================
# Alerting Metrics
# =============================================================================

# Alerts sent
alerts_sent_total = _get_or_create_counter(
    "parasite_alerts_sent_total",
    "Total alerts sent",
    labelnames=["severity", "channel"],
)

# Escalations
escalations_total = _get_or_create_counter(
    "parasite_escalations_total",
    "Total escalations triggered",
    labelnames=["component", "pattern"],
)


# =============================================================================
# Chaos Engineering Metrics
# =============================================================================

# Recovery time from chaos injection
chaos_recovery_seconds = _get_or_create_histogram(
    "parasite_chaos_recovery_seconds",
    "Time to recover from chaos injection",
    labelnames=["experiment_type"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)

# Error budget consumption
chaos_error_budget_consumed = _get_or_create_gauge(
    "parasite_chaos_error_budget_consumed",
    "Error budget consumed during chaos experiment",
    labelnames=["experiment_type"],
)


# =============================================================================
# WebSocket ACK Metrics
# =============================================================================

# ACK timeouts
websocket_ack_timeout_total = _get_or_create_counter(
    "parasite_websocket_ack_timeout_total",
    "Total ACK timeouts",
    labelnames=["connection_id"],
)

# Pending ACKs
websocket_pending_acks = _get_or_create_gauge(
    "parasite_websocket_pending_acks",
    "Number of pending ACKs",
)

# ACK latency
websocket_ack_latency_seconds = _get_or_create_histogram(
    "parasite_websocket_ack_latency_seconds",
    "Time to receive ACK",
    labelnames=["connection_id"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 3.0],
)


# =============================================================================
# Event Bus Metrics
# =============================================================================

# Subscription count by event type
eventbus_subscriptions = _get_or_create_gauge(
    "parasite_eventbus_subscriptions",
    "Active event bus subscriptions",
    labelnames=["event_type"],
)

# Stale subscriptions removed
eventbus_stale_removed_total = _get_or_create_counter(
    "parasite_eventbus_stale_removed_total",
    "Total stale subscriptions removed",
)


# =============================================================================
# Helper Functions
# =============================================================================


def record_detection(
    component: str,
    pattern: str,
    severity: str,
    duration_seconds: float,
    detector_name: str,
) -> None:
    """Record a parasite detection.

    Args:
        component: Component where parasite was detected.
        pattern: Pattern name.
        severity: Severity level.
        duration_seconds: Time to detect.
        detector_name: Name of the detector.
    """
    if METRICS_ENABLED:
        parasite_detected_total.labels(component=component, pattern=pattern, severity=severity).inc()
        detection_duration_seconds.labels(detector=detector_name).observe(duration_seconds)
        active_parasites.labels(component=component).inc()


def record_state_transition(
    from_state: str,
    to_state: str,
    confidence: float,
    duration_in_previous_state: float,
) -> None:
    """Record a state machine transition.

    Args:
        from_state: State before transition.
        to_state: State after transition.
        confidence: Confidence level for the transition.
        duration_in_previous_state: Time spent in previous state.
    """
    if METRICS_ENABLED:
        # Bucket confidence for cardinality control
        if confidence >= 0.95:
            confidence_bucket = "high"
        elif confidence >= 0.80:
            confidence_bucket = "medium"
        else:
            confidence_bucket = "low"

        guard_state_transitions_total.labels(
            from_state=from_state,
            to_state=to_state,
            confidence_bucket=confidence_bucket,
        ).inc()

        # Update current state gauges
        guard_current_state.labels(state=from_state).set(0)
        guard_current_state.labels(state=to_state).set(1)

        # Record duration in previous state
        guard_state_duration_seconds.labels(state=from_state).observe(duration_in_previous_state)


def record_precision_metrics(
    detector_name: str,
    precision: float,
    recall: float,
    f1_score: float,
) -> None:
    """Record precision metrics for a detector.

    Args:
        detector_name: Name of the detector.
        precision: Precision value.
        recall: Recall value.
        f1_score: F1 score.
    """
    if METRICS_ENABLED:
        detection_precision.labels(detector=detector_name).set(precision)
        detection_recall.labels(detector=detector_name).set(recall)
        detection_f1_score.labels(detector=detector_name).set(f1_score)


def record_sanitization(
    component: str,
    success: bool,
    duration_seconds: float,
) -> None:
    """Record a sanitization attempt.

    Args:
        component: Component being sanitized.
        success: Whether sanitization succeeded.
        duration_seconds: Time to sanitize.
    """
    if METRICS_ENABLED:
        sanitization_attempts_total.labels(component=component, success=str(success).lower()).inc()
        sanitization_duration_seconds.labels(component=component).observe(duration_seconds)
        if success:
            active_parasites.labels(component=component).dec()


def record_alert(severity: str, channel: str) -> None:
    """Record an alert being sent.

    Args:
        severity: Alert severity.
        channel: Alert channel used.
    """
    if METRICS_ENABLED:
        alerts_sent_total.labels(severity=severity, channel=channel).inc()


def record_escalation(component: str, pattern: str) -> None:
    """Record an escalation.

    Args:
        component: Component being escalated.
        pattern: Pattern that triggered escalation.
    """
    if METRICS_ENABLED:
        escalations_total.labels(component=component, pattern=pattern).inc()


def record_anomaly(
    component: str,
    z_score: float,
    severity: str,
    threshold: float,
) -> None:
    """Record an anomaly detection.

    Args:
        component: Component where anomaly was detected.
        z_score: Z-score of the anomaly.
        severity: Severity level.
        threshold: Current adaptive threshold.
    """
    if METRICS_ENABLED:
        anomaly_z_score.labels(component=component).observe(z_score)
        anomaly_threshold.labels(component=component).set(threshold)
        anomaly_detected_total.labels(component=component, severity=severity).inc()


def record_chaos_result(
    experiment_type: str,
    recovery_seconds: float,
    error_budget_consumed: float,
) -> None:
    """Record chaos experiment result.

    Args:
        experiment_type: Type of chaos experiment.
        recovery_seconds: Time to recover.
        error_budget_consumed: Error budget consumed.
    """
    if METRICS_ENABLED:
        chaos_recovery_seconds.labels(experiment_type=experiment_type).observe(recovery_seconds)
        chaos_error_budget_consumed.labels(experiment_type=experiment_type).set(error_budget_consumed)
