"""Metrics collection for retry and fallback operations.

Tracks retry attempts, success rates, fallback invocations, and operational
metrics for observability and debugging of error recovery mechanisms.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)

__all__ = [
    "RetryMetrics",
    "MetricsCollector",
    "get_metrics_collector",
]


@dataclass
class OperationMetrics:
    """Metrics for a specific operation type or function."""

    name: str
    """Operation identifier (e.g., 'network.fetch_api', 'file_io.write_config')."""

    total_attempts: int = 0
    """Total number of execution attempts."""

    successful_attempts: int = 0
    """Attempts that succeeded on first try."""

    retry_attempts: int = 0
    """Attempts that required retry."""

    failed_attempts: int = 0
    """Attempts that failed after all retries exhausted."""

    fallback_invocations: int = 0
    """Number of times fallback strategy was triggered."""

    total_retries: int = 0
    """Cumulative count of individual retry steps."""

    last_error: str | None = None
    """Last error message encountered."""

    last_error_time: datetime | None = None
    """Timestamp of last error."""

    def success_rate(self) -> float:
        """Calculate success rate as percentage (0-100).

        Returns:
            Percentage of attempts that succeeded without needing retry.
        """
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_attempts / self.total_attempts) * 100

    def fallback_rate(self) -> float:
        """Calculate fallback invocation rate as percentage (0-100).

        Returns:
            Percentage of attempts requiring fallback.
        """
        if self.total_attempts == 0:
            return 0.0
        return (self.fallback_invocations / self.total_attempts) * 100

    def avg_retries_per_failure(self) -> float:
        """Calculate average retry count per failed attempt.

        Returns:
            Average number of retries when operation fails.
        """
        failures = self.retry_attempts + self.failed_attempts
        if failures == 0:
            return 0.0
        return self.total_retries / failures

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization.

        Returns:
            Dictionary representation of metrics.
        """
        return {
            "name": self.name,
            "total_attempts": self.total_attempts,
            "successful_attempts": self.successful_attempts,
            "retry_attempts": self.retry_attempts,
            "failed_attempts": self.failed_attempts,
            "fallback_invocations": self.fallback_invocations,
            "total_retries": self.total_retries,
            "success_rate_pct": round(self.success_rate(), 2),
            "fallback_rate_pct": round(self.fallback_rate(), 2),
            "avg_retries_per_failure": round(self.avg_retries_per_failure(), 2),
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


@dataclass
class RetryMetrics:
    """Aggregated retry/fallback metrics across all operations."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    """Timestamp when metrics were captured."""

    operations: dict[str, OperationMetrics] = field(default_factory=dict)
    """Per-operation metrics."""

    total_operations_tracked: int = 0
    """Total unique operations tracked."""

    def add_operation_metric(self, metric: OperationMetrics) -> None:
        """Add or update an operation's metrics.

        Args:
            metric: OperationMetrics to track.
        """
        self.operations[metric.name] = metric
        self.total_operations_tracked = len(self.operations)

    def get_operation_metric(self, name: str) -> OperationMetrics | None:
        """Retrieve metrics for a specific operation.

        Args:
            name: Operation identifier.

        Returns:
            OperationMetrics if found, None otherwise.
        """
        return self.operations.get(name)

    def aggregate_success_rate(self) -> float:
        """Calculate overall success rate across all operations.

        Returns:
            Overall success rate as percentage (0-100).
        """
        if not self.operations:
            return 0.0
        total_attempts = sum(m.total_attempts for m in self.operations.values())
        if total_attempts == 0:
            return 0.0
        total_successful = sum(m.successful_attempts for m in self.operations.values())
        return (total_successful / total_attempts) * 100

    def aggregate_fallback_rate(self) -> float:
        """Calculate overall fallback rate across all operations.

        Returns:
            Overall fallback rate as percentage (0-100).
        """
        if not self.operations:
            return 0.0
        total_attempts = sum(m.total_attempts for m in self.operations.values())
        if total_attempts == 0:
            return 0.0
        total_fallbacks = sum(m.fallback_invocations for m in self.operations.values())
        return (total_fallbacks / total_attempts) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization.

        Returns:
            Dictionary representation of all metrics.
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_operations_tracked": self.total_operations_tracked,
            "aggregate_success_rate_pct": round(self.aggregate_success_rate(), 2),
            "aggregate_fallback_rate_pct": round(self.aggregate_fallback_rate(), 2),
            "operations": {
                name: metric.to_dict() for name, metric in self.operations.items()
            },
        }


class MetricsCollector:
    """Thread-safe collector for retry and fallback metrics.

    Aggregates metrics from all retry/fallback operations across the system
    for observability and debugging.
    """

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self._metrics: dict[str, OperationMetrics] = {}
        self._lock = Lock()
        self._reset_time = datetime.now(UTC)

    def record_attempt(
        self,
        operation_name: str,
        success: bool,
        required_retry: bool = False,
        error: Exception | None = None,
    ) -> None:
        """Record an operation attempt.

        Args:
            operation_name: Unique identifier for the operation.
            success: Whether the attempt succeeded.
            required_retry: Whether retry was required.
            error: Exception that occurred, if any.
        """
        with self._lock:
            if operation_name not in self._metrics:
                self._metrics[operation_name] = OperationMetrics(name=operation_name)

            metric = self._metrics[operation_name]
            metric.total_attempts += 1

            if success and not required_retry:
                metric.successful_attempts += 1
            elif success and required_retry:
                metric.retry_attempts += 1
            else:
                metric.failed_attempts += 1

            if error:
                metric.last_error = str(error)
                metric.last_error_time = datetime.now(UTC)

    def record_retry(self, operation_name: str) -> None:
        """Record a retry attempt.

        Args:
            operation_name: Unique identifier for the operation.
        """
        with self._lock:
            if operation_name not in self._metrics:
                self._metrics[operation_name] = OperationMetrics(name=operation_name)
            self._metrics[operation_name].total_retries += 1

    def record_fallback(self, operation_name: str) -> None:
        """Record a fallback invocation.

        Args:
            operation_name: Unique identifier for the operation.
        """
        with self._lock:
            if operation_name not in self._metrics:
                self._metrics[operation_name] = OperationMetrics(name=operation_name)
            self._metrics[operation_name].fallback_invocations += 1

    def get_metrics(self) -> RetryMetrics:
        """Get current aggregated metrics.

        Returns:
            Aggregated RetryMetrics snapshot.
        """
        with self._lock:
            metrics = RetryMetrics()
            for metric in self._metrics.values():
                metrics.add_operation_metric(metric)
            return metrics

    def get_operation_metric(self, operation_name: str) -> OperationMetrics | None:
        """Get metrics for a specific operation.

        Args:
            operation_name: Unique identifier for the operation.

        Returns:
            OperationMetrics if found, None otherwise.
        """
        with self._lock:
            return self._metrics.get(operation_name)

    def reset_metrics(self, older_than: timedelta | None = None) -> int:
        """Reset metrics, optionally only those older than a duration.

        Args:
            older_than: Reset only metrics older than this duration. If None, reset all.

        Returns:
            Number of metrics reset.
        """
        with self._lock:
            if older_than is None:
                count = len(self._metrics)
                self._metrics.clear()
                self._reset_time = datetime.now(UTC)
                return count

            cutoff_time = datetime.now(UTC) - older_than
            old_metrics = [
                name
                for name, metric in self._metrics.items()
                if metric.last_error_time and metric.last_error_time < cutoff_time
            ]
            for name in old_metrics:
                del self._metrics[name]
            return len(old_metrics)

    def export_for_monitoring(self) -> dict[str, Any]:
        """Export metrics in a format suitable for monitoring/alerting.

        Returns:
            Dictionary with metrics ready for Prometheus/monitoring systems.
        """
        metrics = self.get_metrics()
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "reset_time": self._reset_time.isoformat(),
            "uptime_seconds": (datetime.now(UTC) - self._reset_time).total_seconds(),
            "metrics": metrics.to_dict(),
        }


# Global metrics collector instance
_global_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance.

    Returns:
        The global MetricsCollector instance (lazy-initialized).
    """
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector
