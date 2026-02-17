"""
Performance Monitoring Library
New incoming connection to grid_intelligence_library
"""

import asyncio
import json
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import psutil  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""

    name: str
    value: float
    unit: str
    timestamp: datetime
    threshold: float | None = None
    status: str = "normal"  # normal, warning, critical
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationMetrics:
    """Metrics for a specific operation"""

    operation_name: str
    total_calls: int = 0
    total_duration: float = 0.0
    avg_duration: float = 0.0
    min_duration: float = float("inf")
    max_duration: float = 0.0
    error_count: int = 0
    success_rate: float = 1.0
    last_called: datetime | None = None


class PerformanceMonitor:
    """Centralized performance monitoring for GRID system"""

    def __init__(self, config_path: str | None = None):
        self.metrics: dict[str, list[PerformanceMetric]] = {}
        self.operations: dict[str, OperationMetrics] = {}
        self.thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "response_time": 2.0,
            "error_rate": 5.0,
            "success_rate": 95.0,
        }
        self.alerts: list[dict[str, Any]] = []
        self.monitoring_active = False
        self.monitoring_thread: threading.Thread | None = None
        self.config_path = config_path
        self._load_config()

    def _load_config(self):
        """Load configuration from file if provided"""
        if self.config_path and Path(self.config_path).exists():
            try:
                with open(self.config_path) as f:
                    config = json.load(f)
                    self.thresholds.update(config.get("thresholds", {}))
            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}")

    def save_config(self):
        """Save current configuration to file (Synchronous)."""
        if self.config_path:
            try:
                config = {"thresholds": self.thresholds, "saved_at": datetime.now(UTC).isoformat()}
                Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
                with open(self.config_path, "w") as f:
                    json.dump(config, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save config to {self.config_path}: {e}")

    async def collect_system_metrics(self) -> dict[str, PerformanceMetric]:
        """Collect system-level performance metrics"""
        metrics = {}

        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics["cpu_usage"] = PerformanceMetric(
                name="cpu_usage",
                value=cpu_percent,
                unit="percent",
                timestamp=datetime.now(UTC),
                threshold=self.thresholds["cpu_usage"],
                status=self._get_status(cpu_percent, self.thresholds["cpu_usage"]),
                metadata={"cores": psutil.cpu_count()},
            )

            # Memory usage
            memory = psutil.virtual_memory()
            metrics["memory_usage"] = PerformanceMetric(
                name="memory_usage",
                value=memory.percent,
                unit="percent",
                timestamp=datetime.now(UTC),
                threshold=self.thresholds["memory_usage"],
                status=self._get_status(memory.percent, self.thresholds["memory_usage"]),
                metadata={
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "used_gb": memory.used / (1024**3),
                },
            )

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            metrics["disk_usage"] = PerformanceMetric(
                name="disk_usage",
                value=disk_percent,
                unit="percent",
                timestamp=datetime.now(UTC),
                threshold=self.thresholds["disk_usage"],
                status=self._get_status(disk_percent, self.thresholds["disk_usage"]),
                metadata={
                    "total_gb": disk.total / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "free_gb": disk.free / (1024**3),
                },
            )

            # Network I/O
            net_io = psutil.net_io_counters()
            metrics["network_io"] = PerformanceMetric(
                name="network_io",
                value=net_io.bytes_sent + net_io.bytes_recv,
                unit="bytes",
                timestamp=datetime.now(UTC),
                metadata={
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "status": "normal",
                },
            )

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")

        return metrics

    def track_operation_start(self, operation: str, metadata: dict[str, Any] | None = None) -> str:
        """Track the start of an operation"""
        call_id = f"{operation}_{int(time.time() * 1000000)}"

        if operation not in self.operations:
            self.operations[operation] = OperationMetrics(operation_name=operation)

        return call_id

    def track_operation_end(self, operation: str, call_id: str, success: bool = True, error: str | None = None):
        """Track the end of an operation"""
        if operation not in self.operations:
            self.operations[operation] = OperationMetrics(operation_name=operation)

        op_metrics = self.operations[operation]

        # Extract timestamp from call_id (rough estimation)
        try:
            start_timestamp = int(call_id.split("_")[-1]) / 1000000
            duration = time.time() - start_timestamp
        except Exception:
            duration = 0.0

        # Update operation metrics
        op_metrics.total_calls += 1
        op_metrics.total_duration += duration
        op_metrics.avg_duration = op_metrics.total_duration / op_metrics.total_calls
        op_metrics.min_duration = min(op_metrics.min_duration, duration)
        op_metrics.max_duration = max(op_metrics.max_duration, duration)
        op_metrics.last_called = datetime.now(UTC)

        if not success:
            op_metrics.error_count += 1

        op_metrics.success_rate = ((op_metrics.total_calls - op_metrics.error_count) / op_metrics.total_calls) * 100

        # Create performance metric
        metric = PerformanceMetric(
            name=f"{operation}_duration",
            value=duration,
            unit="seconds",
            timestamp=datetime.now(UTC),
            threshold=self.thresholds.get("response_time"),
            status=self._get_status(duration, self.thresholds.get("response_time", 2.0)),
            metadata={"operation": operation, "success": success, "error": error, "call_id": call_id},
        )

        if operation not in self.metrics:
            self.metrics[operation] = []

        self.metrics[operation].append(metric)

        # Keep only last 100 metrics per operation
        if len(self.metrics[operation]) > 100:
            self.metrics[operation] = self.metrics[operation][-100:]

        # Check for alerts
        self._check_alerts(metric)

    def track_function_performance(self, func: Callable) -> Callable:
        """Decorator to track function performance"""

        def wrapper(*args, **kwargs):
            call_id = self.track_operation_start(func.__name__)
            time.time()

            try:
                result = func(*args, **kwargs)
                self.track_operation_end(func.__name__, call_id, success=True)
                return result
            except Exception as e:
                self.track_operation_end(func.__name__, call_id, success=False, error=str(e))
                raise

        return wrapper

    def _get_status(self, value: float, threshold: float) -> str:
        """Determine metric status based on threshold"""
        if value >= threshold:
            return "critical"
        elif value >= threshold * 0.8:
            return "warning"
        return "normal"

    def _check_alerts(self, metric: PerformanceMetric):
        """Check if metric should trigger an alert"""
        if metric.status in ["warning", "critical"]:
            alert = {
                "timestamp": metric.timestamp.isoformat(),
                "metric_name": metric.name,
                "status": metric.status,
                "value": metric.value,
                "threshold": metric.threshold,
                "message": f"{metric.name} is {metric.status}: {metric.value}{metric.unit}",
            }

            self.alerts.append(alert)

            # Keep only last 100 alerts
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]

            logger.warning(alert["message"])

    def get_performance_summary(self) -> dict[str, Any]:
        """Generate performance summary for intelligence library"""
        summary = {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_metrics": len(self.metrics),
            "total_operations": len(self.operations),
            "critical_alerts": 0,
            "warning_alerts": 0,
            "system_health": "healthy",
            "recommendations": [],
            "operations_summary": {},
        }

        # Count alerts
        for alert in self.alerts:
            if alert["status"] == "critical":
                summary["critical_alerts"] += 1
            elif alert["status"] == "warning":
                summary["warning_alerts"] += 1

        # Determine system health
        if summary["critical_alerts"] > 0:
            summary["system_health"] = "critical"
        elif summary["warning_alerts"] > 5:
            summary["system_health"] = "degraded"
        elif summary["warning_alerts"] > 0:
            summary["system_health"] = "warning"

        # Operation summaries
        for op_name, op_metrics in self.operations.items():
            summary["operations_summary"][op_name] = {
                "total_calls": op_metrics.total_calls,
                "avg_duration": op_metrics.avg_duration,
                "success_rate": op_metrics.success_rate,
                "error_count": op_metrics.error_count,
                "last_called": op_metrics.last_called.isoformat() if op_metrics.last_called else None,
            }

            # Generate recommendations
            if op_metrics.success_rate < self.thresholds["success_rate"]:
                summary["recommendations"].append(f"Low success rate for {op_name}: {op_metrics.success_rate:.1f}%")

            if op_metrics.avg_duration > self.thresholds["response_time"]:
                summary["recommendations"].append(f"Slow response time for {op_name}: {op_metrics.avg_duration:.2f}s")

        # System-level recommendations
        recent_alerts = [
            a for a in self.alerts if datetime.fromisoformat(a["timestamp"]) > datetime.now(UTC) - timedelta(hours=1)
        ]

        if len(recent_alerts) > 10:
            summary["recommendations"].append("High alert frequency detected - investigate system stability")

        return summary

    def get_operation_trends(self, operation: str, hours: int = 24) -> dict[str, Any]:
        """Get performance trends for a specific operation"""
        if operation not in self.metrics:
            return {"error": f"No metrics found for operation: {operation}"}

        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics[operation] if m.timestamp > cutoff_time]

        if not recent_metrics:
            return {"error": f"No recent metrics found for operation: {operation}"}

        values = [m.value for m in recent_metrics]

        return {
            "operation": operation,
            "timeframe_hours": hours,
            "sample_count": len(recent_metrics),
            "avg_value": sum(values) / len(values),
            "min_value": min(values),
            "max_value": max(values),
            "trend": self._calculate_trend(values),
            "status_distribution": self._get_status_distribution(recent_metrics),
        }

    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "insufficient_data"

        # Simple linear regression to determine trend
        n = len(values)
        x = list(range(n))
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)

        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"

    def _get_status_distribution(self, metrics: list[PerformanceMetric]) -> dict[str, int]:
        """Get distribution of metric statuses"""
        distribution = {"normal": 0, "warning": 0, "critical": 0}
        for metric in metrics:
            distribution[metric.status] += 1
        return distribution

    def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring in background thread"""
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return

        self.monitoring_active = True

        def monitor_loop():
            while self.monitoring_active:
                try:
                    asyncio.run(self.collect_system_metrics())
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")
                    time.sleep(interval)

        self.monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info(f"Started performance monitoring with {interval}s interval")

    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Stopped performance monitoring")

    def export_metrics(self, filepath: str, format: str = "json"):
        """Export metrics to file (Synchronous)."""
        data = {
            "export_timestamp": datetime.now(UTC).isoformat(),
            "metrics": {
                name: [
                    {
                        "name": m.name,
                        "value": m.value,
                        "unit": m.unit,
                        "timestamp": m.timestamp.isoformat(),
                        "threshold": m.threshold,
                        "status": m.status,
                        "metadata": m.metadata,
                    }
                    for m in metrics
                ]
                for name, metrics in self.metrics.items()
            },
            "operations": {
                name: {
                    "operation_name": op.operation_name,
                    "total_calls": op.total_calls,
                    "total_duration": op.total_duration,
                    "avg_duration": op.avg_duration,
                    "min_duration": op.min_duration,
                    "max_duration": op.max_duration,
                    "error_count": op.error_count,
                    "success_rate": op.success_rate,
                    "last_called": op.last_called.isoformat() if op.last_called else None,
                }
                for name, op in self.operations.items()
            },
            "alerts": self.alerts[-50:],  # Last 50 alerts
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "json":
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info(f"Exported metrics to {filepath}")


# Integration with grid_intelligence_library
def register_with_intelligence_library():
    """Register performance monitoring with main intelligence hub"""
    try:
        # This would connect to your actual intelligence library
        # For now, we'll create a mock registration
        monitor = PerformanceMonitor()

        # Mock registration - replace with actual implementation
        registration_info = {
            "source": "performance_monitoring_library",
            "capabilities": [
                "system_metrics",
                "operation_tracking",
                "performance_analysis",
                "alert_generation",
                "trend_analysis",
            ],
            "data_types": ["PerformanceMetric", "OperationMetrics", "SystemAlert", "PerformanceTrend"],
            "endpoints": {
                "summary": "get_performance_summary",
                "trends": "get_operation_trends",
                "export": "export_metrics",
            },
            "registered_at": datetime.now(UTC).isoformat(),
        }

        logger.info(f"Registered performance monitoring library: {registration_info}")
        return monitor

    except Exception as e:
        logger.error(f"Failed to register with intelligence library: {e}")
        return PerformanceMonitor()


# Context manager for operation tracking
class OperationTracker:
    """Context manager for tracking operations"""

    def __init__(self, monitor: PerformanceMonitor, operation: str, metadata: dict[str, Any] | None = None):
        self.monitor = monitor
        self.operation = operation
        self.metadata = metadata or {}
        self.call_id = None
        self.start_time = None

    def __enter__(self):
        self.call_id = self.monitor.track_operation_start(self.operation, self.metadata)
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        success = exc_type is None
        error = str(exc_val) if exc_val else None
        if self.call_id is not None:
            self.monitor.track_operation_end(self.operation, self.call_id, success, error)


# Singleton instance
_global_monitor: PerformanceMonitor | None = None


def get_global_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = register_with_intelligence_library()
    return _global_monitor


def track_performance(operation: str):
    """Decorator for tracking function performance"""
    monitor = get_global_monitor()
    return monitor.track_function_performance
