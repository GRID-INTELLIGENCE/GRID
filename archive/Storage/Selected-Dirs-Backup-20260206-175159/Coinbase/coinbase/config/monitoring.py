"""
Monitoring and Alerting Module
==============================
Application health checks, performance metrics, and error tracking.

Usage:
    from coinbase.config.monitoring import HealthChecker, MetricsCollector

    # Health checks
    health = HealthChecker()
    status = health.check_all()

    # Metrics collection
    metrics = MetricsCollector()
    metrics.record_latency('api_call', 0.5)
"""

import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: dict[str, Any] | None = None
    latency_ms: float | None = None


@dataclass
class MetricPoint:
    """Single metric data point."""

    name: str
    value: float
    timestamp: datetime
    labels: dict[str, str] = field(default_factory=dict)


class HealthChecker:
    """
    Application health checker.

    Performs health checks on various components and reports status.
    """

    def __init__(self) -> None:
        """Initialize health checker."""
        self.checks: dict[str, Callable[[], HealthCheckResult]] = {}
        self._register_default_checks()

    def _register_default_checks(self) -> None:
        """Register default health checks."""
        self.register_check("databricks", self._check_databricks)
        self.register_check("memory", self._check_memory)
        self.register_check("disk", self._check_disk)

    def register_check(self, name: str, check_func: Callable[[], HealthCheckResult]) -> None:
        """
        Register a health check.

        Args:
            name: Check name
            check_func: Function that returns HealthCheckResult
        """
        self.checks[name] = check_func

    def check_all(self) -> dict[str, HealthCheckResult]:
        """
        Run all health checks.

        Returns:
            Dictionary of check results
        """
        results = {}
        for name, check_func in self.checks.items():
            try:
                start_time = time.time()
                result = check_func()
                result.latency_ms = (time.time() - start_time) * 1000
                results[name] = result
            except Exception as e:
                results[name] = HealthCheckResult(
                    name=name, status=HealthStatus.UNHEALTHY, message=f"Check failed: {str(e)}"
                )
        return results

    def get_overall_status(
        self, results: dict[str, HealthCheckResult] | None = None
    ) -> HealthStatus:
        """
        Get overall health status.

        Args:
            results: Optional pre-computed results

        Returns:
            Overall health status
        """
        if results is None:
            results = self.check_all()

        statuses = [r.status for r in results.values()]

        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    def _check_databricks(self) -> HealthCheckResult:
        """Check Databricks connectivity."""
        try:
            import os

            host = os.getenv("DATABRICKS_HOST")
            if not host:
                return HealthCheckResult(
                    name="databricks",
                    status=HealthStatus.UNHEALTHY,
                    message="DATABRICKS_HOST not configured",
                )

            # TODO: Implement actual connectivity check
            return HealthCheckResult(
                name="databricks",
                status=HealthStatus.HEALTHY,
                message="Databricks configured",
                details={"host": host},
            )
        except Exception as e:
            return HealthCheckResult(
                name="databricks",
                status=HealthStatus.UNHEALTHY,
                message=f"Databricks check failed: {str(e)}",
            )

    def _check_memory(self) -> HealthCheckResult:
        """Check memory usage."""
        try:
            import psutil  # type: ignore

            memory = psutil.virtual_memory()
            usage_percent = memory.percent

            if usage_percent > 90:
                status = HealthStatus.UNHEALTHY
            elif usage_percent > 75:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY

            return HealthCheckResult(
                name="memory",
                status=status,
                message=f"Memory usage: {usage_percent}%",
                details={
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "percent": usage_percent,
                },
            )
        except ImportError:
            return HealthCheckResult(
                name="memory",
                status=HealthStatus.HEALTHY,
                message="Memory check skipped (psutil not installed)",
            )

    def _check_disk(self) -> HealthCheckResult:
        """Check disk usage."""
        try:
            import psutil

            disk = psutil.disk_usage("/")
            usage_percent = disk.percent

            if usage_percent > 90:
                status = HealthStatus.UNHEALTHY
            elif usage_percent > 80:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY

            return HealthCheckResult(
                name="disk",
                status=status,
                message=f"Disk usage: {usage_percent}%",
                details={
                    "total_gb": disk.total / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "percent": usage_percent,
                },
            )
        except ImportError:
            return HealthCheckResult(
                name="disk",
                status=HealthStatus.HEALTHY,
                message="Disk check skipped (psutil not installed)",
            )


class MetricsCollector:
    """
    Performance metrics collector.

    Collects and stores metrics for monitoring and alerting.
    """

    def __init__(self, max_history: int = 10000):
        """
        Initialize metrics collector.

        Args:
            max_history: Maximum number of data points to keep per metric
        """
        self.max_history = max_history
        self.metrics: dict[str, deque] = {}
        self._lock = threading.Lock()

    def record(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """
        Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels/tags
        """
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = deque(maxlen=self.max_history)

            point = MetricPoint(
                name=name, value=value, timestamp=datetime.now(), labels=labels or {}
            )
            self.metrics[name].append(point)

    def record_latency(
        self, operation: str, latency_seconds: float, labels: dict[str, str] | None = None
    ) -> None:
        """
        Record operation latency.

        Args:
            operation: Operation name
            latency_seconds: Latency in seconds
            labels: Optional labels
        """
        all_labels = labels or {}
        all_labels["type"] = "latency"
        self.record(
            f"{operation}_latency", latency_seconds * 1000, all_labels
        )  # Store as milliseconds

    def record_count(
        self, name: str, increment: int = 1, labels: dict[str, str] | None = None
    ) -> None:
        """
        Record a counter metric.

        Args:
            name: Counter name
            increment: Amount to increment
            labels: Optional labels
        """
        all_labels = labels or {}
        all_labels["type"] = "counter"
        self.record(name, increment, all_labels)

    def record_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """
        Record a gauge metric.

        Args:
            name: Gauge name
            value: Current value
            labels: Optional labels
        """
        all_labels = labels or {}
        all_labels["type"] = "gauge"
        self.record(name, value, all_labels)

    def get_stats(self, name: str, window_seconds: int | None = None) -> dict[str, float] | None:
        """
        Get statistics for a metric.

        Args:
            name: Metric name
            window_seconds: Optional time window (default: all data)

        Returns:
            Statistics dictionary or None if no data
        """
        with self._lock:
            if name not in self.metrics:
                return None

            points = self.metrics[name]
            if not points:
                return None

            # Filter by time window if specified
            if window_seconds:
                cutoff = datetime.now() - timedelta(seconds=window_seconds)
                values = [p.value for p in points if p.timestamp > cutoff]
            else:
                values = [p.value for p in points]

            if not values:
                return None

            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
                "last": values[-1],
            }

    def get_all_metrics(self) -> list[str]:
        """Get list of all metric names."""
        with self._lock:
            return list(self.metrics.keys())


class AlertManager:
    """
    Alert manager for triggering notifications.

    Monitors metrics and health checks and triggers alerts when thresholds are exceeded.
    """

    def __init__(self) -> None:
        """Initialize alert manager."""
        self.rules: list[dict[str, Any]] = []
        self.alert_handlers: list[Callable[[dict[str, Any]], None]] = []
        self._running = False
        self._thread: threading.Thread | None = None

    def add_rule(self, name: str, condition: Callable[[], bool], message: str) -> None:
        """
        Add an alert rule.

        Args:
            name: Rule name
            condition: Function that returns True when alert should fire
            message: Alert message
        """
        self.rules.append(
            {"name": name, "condition": condition, "message": message, "last_alert": None}
        )

    def add_handler(self, handler: Callable[[dict[str, Any]], None]) -> None:
        """
        Add an alert handler.

        Args:
            handler: Function to call when alert fires
        """
        self.alert_handlers.append(handler)

    def start(self, interval_seconds: int = 60) -> None:
        """
        Start alert monitoring.

        Args:
            interval_seconds: Check interval
        """
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor, args=(interval_seconds,), daemon=True)
        self._thread.start()
        logger.info(f"Alert manager started with {interval_seconds}s interval")

    def stop(self) -> None:
        """Stop alert monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Alert manager stopped")

    def _monitor(self, interval_seconds: int) -> None:
        """Monitor loop."""
        while self._running:
            try:
                self._check_rules()
            except Exception as e:
                logger.error(f"Error checking alert rules: {e}")

            time.sleep(interval_seconds)

    def _check_rules(self) -> None:
        """Check all alert rules."""
        for rule in self.rules:
            try:
                if rule["condition"]():
                    # Check cooldown (min 5 minutes between alerts)
                    if rule["last_alert"] and (datetime.now() - rule["last_alert"]).seconds < 300:
                        continue

                    rule["last_alert"] = datetime.now()
                    alert = {
                        "name": rule["name"],
                        "message": rule["message"],
                        "timestamp": datetime.now(),
                    }

                    for handler in self.alert_handlers:
                        try:
                            handler(alert)
                        except Exception as e:
                            logger.error(f"Alert handler error: {e}")
            except Exception as e:
                logger.error(f"Error checking rule {rule['name']}: {e}")


# Global instances
_global_health_checker: HealthChecker | None = None
_global_metrics: MetricsCollector | None = None
_global_alerts: AlertManager | None = None


def get_health_checker() -> HealthChecker:
    """Get global health checker instance."""
    global _global_health_checker
    if _global_health_checker is None:
        _global_health_checker = HealthChecker()
    return _global_health_checker


def get_metrics() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector()
    return _global_metrics


def get_alert_manager() -> AlertManager:
    """Get global alert manager instance."""
    global _global_alerts
    if _global_alerts is None:
        _global_alerts = AlertManager()
    return _global_alerts
