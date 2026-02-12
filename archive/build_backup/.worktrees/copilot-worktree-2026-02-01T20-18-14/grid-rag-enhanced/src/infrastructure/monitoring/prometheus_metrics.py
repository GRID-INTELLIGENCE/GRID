"""
Prometheus metrics integration for GRID.

Provides comprehensive metrics collection, exposition, and monitoring
integration with Prometheus. Includes custom metrics collectors,
metric definitions, and monitoring endpoints.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# Try to import prometheus_client, but make it optional
try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Summary,
        generate_latest,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create dummy classes for type hints
    Counter = Gauge = Histogram = Summary = CollectorRegistry = object
    def generate_latest():
        return b""
    CONTENT_TYPE_LATEST = "text/plain"


class MetricType(Enum):
    """Prometheus metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricDefinition:
    """Metric definition."""
    name: str
    metric_type: MetricType
    description: str
    labels: set[str]
    unit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "metric_type": self.metric_type.value,
            "description": self.description,
            "labels": list(self.labels),
            "unit": self.unit,
        }


class PrometheusMetricsCollector:
    """
    Prometheus metrics collector for GRID.

    Features:
    - Custom metric definitions
    - Automatic metric collection
    - Label-based metric organization
    - Performance metrics
    - Business metrics
    - System metrics
    - Error tracking
    """

    def __init__(self, registry: CollectorRegistry | None = None):
        """
        Initialize Prometheus metrics collector.

        Args:
            registry: Prometheus registry instance
        """
        if not PROMETHEUS_AVAILABLE:
            logger.warning("prometheus_client not available, metrics will be disabled")
            self.enabled = False
            return

        self.enabled = True
        self.registry = registry or CollectorRegistry()

        # Metric storage
        self._metrics: dict[str, Any] = {}
        self._metric_definitions: dict[str, MetricDefinition] = {}

        # Initialize default metrics
        self._initialize_default_metrics()

        logger.info("PrometheusMetricsCollector initialized")

    def define_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str,
        labels: set[str] | None = None,
        unit: str | None = None,
    ) -> bool:
        """
        Define a new metric.

        Args:
            name: Metric name
            metric_type: Type of metric
            description: Metric description
            labels: Metric labels
            unit: Metric unit

        Returns:
            True if defined successfully
        """
        if not self.enabled:
            return False

        if name in self._metrics:
            logger.warning(f"Metric {name} already defined")
            return False

        # Create metric based on type
        try:
            if metric_type == MetricType.COUNTER:
                metric = Counter(name, description, list(labels or []), registry=self.registry)
            elif metric_type == MetricType.GAUGE:
                metric = Gauge(name, description, list(labels or []), registry=self.registry)
            elif metric_type == MetricType.HISTOGRAM:
                metric = Histogram(name, description, list(labels or []), registry=self.registry)
            elif metric_type == MetricType.SUMMARY:
                metric = Summary(name, description, list(labels or []), registry=self.registry)
            else:
                logger.error(f"Unknown metric type: {metric_type}")
                return False

            self._metrics[name] = metric
            self._metric_definitions[name] = MetricDefinition(
                name=name,
                metric_type=metric_type,
                description=description,
                labels=labels or set(),
                unit=unit,
            )

            logger.info(f"Defined metric: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to define metric {name}: {e}")
            return False

    def increment_counter(
        self, name: str, value: float = 1.0, labels: dict[str, str] | None = None
    ) -> bool:
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Increment value
            labels: Metric labels

        Returns:
            True if incremented successfully
        """
        if not self.enabled:
            return False

        metric = self._metrics.get(name)
        if not metric or not hasattr(metric, 'inc'):
            logger.error(f"Counter metric {name} not found or not a counter")
            return False

        try:
            if labels:
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)
            return True
        except Exception as e:
            logger.error(f"Failed to increment counter {name}: {e}")
            return False

    def set_gauge(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> bool:
        """
        Set a gauge metric value.

        Args:
            name: Metric name
            value: Gauge value
            labels: Metric labels

        Returns:
            True if set successfully
        """
        if not self.enabled:
            return False

        metric = self._metrics.get(name)
        if not metric or not hasattr(metric, 'set'):
            logger.error(f"Gauge metric {name} not found or not a gauge")
            return False

        try:
            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)
            return True
        except Exception as e:
            logger.error(f"Failed to set gauge {name}: {e}")
            return False

    def observe_histogram(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> bool:
        """
        Observe a histogram metric value.

        Args:
            name: Metric name
            value: Observed value
            labels: Metric labels

        Returns:
            True if observed successfully
        """
        if not self.enabled:
            return False

        metric = self._metrics.get(name)
        if not metric or not hasattr(metric, 'observe'):
            logger.error(f"Histogram metric {name} not found or not a histogram")
            return False

        try:
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)
            return True
        except Exception as e:
            logger.error(f"Failed to observe histogram {name}: {e}")
            return False

    def observe_summary(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> bool:
        """
        Observe a summary metric value.

        Args:
            name: Metric name
            value: Observed value
            labels: Metric labels

        Returns:
            True if observed successfully
        """
        if not self.enabled:
            return False

        metric = self._metrics.get(name)
        if not metric or not hasattr(metric, 'observe'):
            logger.error(f"Summary metric {name} not found or not a summary")
            return False

        try:
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)
            return True
        except Exception as e:
            logger.error(f"Failed to observe summary {name}: {e}")
            return False

    def get_metrics(self) -> dict[str, MetricDefinition]:
        """Get all metric definitions."""
        return self._metric_definitions.copy()

    def get_metric_names(self) -> list[str]:
        """Get all metric names."""
        return list(self._metrics.keys())

    def generate_metrics(self) -> bytes:
        """Generate Prometheus metrics output."""
        if not self.enabled:
            return b"# Metrics disabled - prometheus_client not available\n"

        try:
            return generate_latest(self.registry)
        except Exception as e:
            logger.error(f"Failed to generate metrics: {e}")
            return b"# Error generating metrics\n"

    def reset_metric(self, name: str) -> bool:
        """
        Reset a metric to its initial state.

        Args:
            name: Metric name

        Returns:
            True if reset successfully
        """
        if not self.enabled:
            return False

        metric = self._metrics.get(name)
        if not metric:
            logger.error(f"Metric {name} not found")
            return False

        try:
            if hasattr(metric, 'clear'):
                metric.clear()
            else:
                logger.warning(f"Metric {name} does not support clearing")
            return True
        except Exception as e:
            logger.error(f"Failed to reset metric {name}: {e}")
            return False

    def _initialize_default_metrics(self) -> None:
        """Initialize default GRID metrics."""
        if not self.enabled:
            return

        # System metrics
        self.define_metric(
            "grid_system_uptime_seconds",
            MetricType.GAUGE,
            "System uptime in seconds",
            {"instance"},
            "seconds"
        )

        self.define_metric(
            "grid_system_memory_usage_bytes",
            MetricType.GAUGE,
            "System memory usage in bytes",
            {"instance"},
            "bytes"
        )

        self.define_metric(
            "grid_system_cpu_usage_percent",
            MetricType.GAUGE,
            "System CPU usage percentage",
            {"instance"},
            "percent"
        )

        # Event metrics
        self.define_metric(
            "grid_events_total",
            MetricType.COUNTER,
            "Total number of events processed",
            {"event_type", "status"},
        )

        self.define_metric(
            "grid_event_processing_duration_seconds",
            MetricType.HISTOGRAM,
            "Event processing duration in seconds",
            {"event_type"},
            "seconds"
        )

        # Skill metrics
        self.define_metric(
            "grid_skills_executed_total",
            MetricType.COUNTER,
            "Total number of skill executions",
            {"skill_id", "status"},
        )

        self.define_metric(
            "grid_skill_execution_duration_seconds",
            MetricType.HISTOGRAM,
            "Skill execution duration in seconds",
            {"skill_id"},
            "seconds"
        )

        self.define_metric(
            "grid_skill_memory_usage_bytes",
            MetricType.HISTOGRAM,
            "Skill memory usage in bytes",
            {"skill_id"},
            "bytes"
        )

        # Security metrics
        self.define_metric(
            "grid_security_alerts_total",
            MetricType.COUNTER,
            "Total number of security alerts",
            {"alert_type", "severity"},
        )

        self.define_metric(
            "grid_security_vulnerabilities_total",
            MetricType.COUNTER,
            "Total number of security vulnerabilities",
            {"severity", "category"},
        )

        # Knowledge graph metrics
        self.define_metric(
            "grid_knowledge_entities_total",
            MetricType.GAUGE,
            "Total number of knowledge graph entities",
            {"entity_type"},
        )

        self.define_metric(
            "grid_knowledge_relationships_total",
            MetricType.GAUGE,
            "Total number of knowledge graph relationships",
            {"relationship_type"},
        )

        self.define_metric(
            "grid_knowledge_query_duration_seconds",
            MetricType.HISTOGRAM,
            "Knowledge graph query duration in seconds",
            {"query_type"},
            "seconds"
        )

        # API metrics
        self.define_metric(
            "grid_api_requests_total",
            MetricType.COUNTER,
            "Total number of API requests",
            {"method", "endpoint", "status"},
        )

        self.define_metric(
            "grid_api_request_duration_seconds",
            MetricType.HISTOGRAM,
            "API request duration in seconds",
            {"method", "endpoint"},
            "seconds"
        )

        # Error metrics
        self.define_metric(
            "grid_errors_total",
            MetricType.COUNTER,
            "Total number of errors",
            {"error_type", "component"},
        )

        self.define_metric(
            "grid_error_rate_percent",
            MetricType.GAUGE,
            "Error rate percentage",
            {"component"},
            "percent"
        )

        # Cognitive Architecture Metrics
        self.define_metric(
            "cognitive_load",
            MetricType.GAUGE,
            "Current cognitive load estimation (0-10 scale)",
            {"user_id", "domain"},
        )
        self.define_metric(
            "processing_mode",
            MetricType.GAUGE,
            "Current processing mode (0=System1, 1=System2)",
            {"user_id"},
        )
        self.define_metric(
            "pattern_detection_latency",
            MetricType.HISTOGRAM,
            "Latency of pattern detection in milliseconds",
            {"pattern_type"},
        )
        self.define_metric(
            "alignment_score",
            MetricType.GAUGE,
            "Current cognitive architecture alignment score (0-1)",
            {"component"},
        )
        self.define_metric(
            "adaptive_response_effectiveness",
            MetricType.GAUGE,
            "Effectiveness of adaptive responses (0-1)",
            {"response_type"},
        )
        self.define_metric(
            "temporal_integration",
            MetricType.GAUGE,
            "Level of temporal pattern integration (0-1)",
            {"pattern_type"},
        )


# Global metrics collector instance
_global_metrics_collector: PrometheusMetricsCollector | None = None


def get_prometheus_metrics_collector() -> PrometheusMetricsCollector:
    """Get or create global Prometheus metrics collector."""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = PrometheusMetricsCollector()
    return _global_metrics_collector


def set_prometheus_metrics_collector(collector: PrometheusMetricsCollector) -> None:
    """Set global Prometheus metrics collector."""
    global _global_metrics_collector
    _global_metrics_collector = collector
