"""
Prometheus metrics for the safety enforcement pipeline.

Exposes counters, histograms, and gauges required by the observability spec.
Import and use these metric objects directly; they are module-level singletons.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, Info

# ---------------------------------------------------------------------------
# Service info
# ---------------------------------------------------------------------------
SAFETY_SERVICE_INFO = Info(
    "safety_service",
    "Safety enforcement service metadata",
)

# ---------------------------------------------------------------------------
# Request-level metrics
# ---------------------------------------------------------------------------
REQUESTS_TOTAL = Counter(
    "safety_requests_total",
    "Total requests processed by the safety pipeline",
    ["outcome"],  # queued | refused | rate_limited
)

REFUSALS_TOTAL = Counter(
    "safety_refusals_total",
    "Total deterministic refusals by reason code",
    ["reason_code"],
)

RATE_LIMITED_TOTAL = Counter(
    "safety_rate_limited_total",
    "Total requests rejected by rate limiter",
    ["trust_tier"],
)

# ---------------------------------------------------------------------------
# Detection metrics
# ---------------------------------------------------------------------------
PRECHECK_LATENCY = Histogram(
    "safety_precheck_latency_seconds",
    "Latency of synchronous pre-check detector",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25),
)

POSTCHECK_LATENCY = Histogram(
    "safety_postcheck_latency_seconds",
    "Latency of post-inference detector",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

DETECTION_LATENCY = Histogram(
    "safety_detection_latency_seconds",
    "Combined detection latency (pre + post)",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# ---------------------------------------------------------------------------
# Escalation metrics
# ---------------------------------------------------------------------------
ESCALATIONS_TOTAL = Counter(
    "safety_escalations_total",
    "Total escalations by severity",
    ["severity"],  # low | medium | high | critical
)

ESCALATION_RESOLUTION_LATENCY = Histogram(
    "safety_escalation_resolution_seconds",
    "Time from escalation creation to human resolution",
    buckets=(60, 300, 600, 1800, 3600, 7200, 14400, 86400),
)

# ---------------------------------------------------------------------------
# Worker metrics
# ---------------------------------------------------------------------------
WORKER_JOBS_PROCESSED = Counter(
    "safety_worker_jobs_processed_total",
    "Total jobs processed by inference workers",
    ["result"],  # passed | flagged | error
)

WORKER_QUEUE_DEPTH = Gauge(
    "safety_worker_queue_depth",
    "Current depth of the inference stream queue",
)

MODEL_CALL_LATENCY = Histogram(
    "safety_model_call_latency_seconds",
    "Latency of model inference calls",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

# ---------------------------------------------------------------------------
# Infrastructure health
# ---------------------------------------------------------------------------
REDIS_HEALTHY = Gauge(
    "safety_redis_healthy",
    "Whether Redis is reachable (1=healthy, 0=unhealthy)",
)

AUDIT_DB_HEALTHY = Gauge(
    "safety_audit_db_healthy",
    "Whether the audit database is reachable (1=healthy, 0=unhealthy)",
)

DETECTOR_HEALTHY = Gauge(
    "safety_detector_healthy",
    "Whether detectors are operational (1=healthy, 0=unhealthy)",
)

# ---------------------------------------------------------------------------
# False positive tracking
# ---------------------------------------------------------------------------
FALSE_POSITIVES_TOTAL = Counter(
    "safety_false_positives_total",
    "Escalations resolved as false positives (approved by reviewer)",
    ["reason_code"],
)


def record_service_info(version: str, environment: str) -> None:
    """Set service info labels once at startup."""
    SAFETY_SERVICE_INFO.info({"version": version, "environment": environment})
