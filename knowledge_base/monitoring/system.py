"""
Knowledge Base Monitoring and Analytics
========================================

Comprehensive monitoring system for tracking usage, performance, and health
metrics of the GRID Knowledge Base system.
"""

import json
import logging
import platform
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import psutil

from ..core.config import KnowledgeBaseConfig

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Individual metric data point."""
    timestamp: datetime
    value: float
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSeries:
    """Time series data for a metric."""
    name: str
    points: deque = field(default_factory=lambda: deque(maxlen=1000))
    tags: dict[str, str] = field(default_factory=dict)

    def add_point(self, value: float, tags: dict[str, str] | None = None) -> None:
        """Add a data point to the series."""
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            tags=tags or {}
        )
        self.points.append(point)

    def get_recent_points(self, hours: int = 24) -> list[MetricPoint]:
        """Get points from the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [p for p in self.points if p.timestamp >= cutoff]

    def get_stats(self) -> dict[str, Any]:
        """Get statistics for this metric series."""
        points = list(self.points)
        if not points:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}

        values = [p.value for p in points]
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "latest": values[-1] if values else 0
        }


class MetricsCollector:
    """Collects and manages system metrics."""

    def __init__(self, config: KnowledgeBaseConfig):
        self.config = config
        self.metrics: dict[str, MetricSeries] = {}
        self._lock = threading.Lock()

        # Initialize standard metrics
        self._init_standard_metrics()

        # Start background collection if enabled
        if config.monitoring.enable_metrics:
            self._start_background_collection()

    def _init_standard_metrics(self) -> None:
        """Initialize standard metric series."""
        standard_metrics = [
            "kb.search.requests",
            "kb.search.latency",
            "kb.search.errors",
            "kb.generation.requests",
            "kb.generation.latency",
            "kb.generation.tokens",
            "kb.generation.errors",
            "kb.ingestion.documents",
            "kb.ingestion.chunks",
            "kb.ingestion.errors",
            "kb.system.cpu_percent",
            "kb.system.memory_percent",
            "kb.system.disk_usage"
        ]

        for metric_name in standard_metrics:
            self.metrics[metric_name] = MetricSeries(metric_name)

    def _start_background_collection(self) -> None:
        """Start background metric collection."""
        def collect_system_metrics():
            while True:
                try:
                    # CPU usage
                    self.record_metric("kb.system.cpu_percent", psutil.cpu_percent(interval=1))

                    # Memory usage
                    memory = psutil.virtual_memory()
                    self.record_metric("kb.system.memory_percent", memory.percent)

                    # Disk usage (for current drive)
                    disk = psutil.disk_usage('/')
                    self.record_metric("kb.system.disk_usage", disk.percent)

                except Exception as e:
                    logger.error(f"System metrics collection failed: {e}")

                time.sleep(60)  # Collect every minute

        thread = threading.Thread(target=collect_system_metrics, daemon=True)
        thread.start()
        logger.info("Background metrics collection started")

    def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a metric value."""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = MetricSeries(name)

            self.metrics[name].add_point(value, tags)

    def get_metric(self, name: str) -> MetricSeries | None:
        """Get a metric series."""
        return self.metrics.get(name)

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """Get all metrics with their statistics."""
        result = {}
        with self._lock:
            for name, series in self.metrics.items():
                result[name] = series.get_stats()
                result[name]["tags"] = series.tags

        return result

    def get_metric_history(self, name: str, hours: int = 24) -> list[dict[str, Any]]:
        """Get historical data for a metric."""
        series = self.get_metric(name)
        if not series:
            return []

        points = series.get_recent_points(hours)
        return [{
            "timestamp": p.timestamp.isoformat(),
            "value": p.value,
            "tags": p.tags
        } for p in points]


class EventLogger:
    """Logs and tracks system events."""

    def __init__(self, config: KnowledgeBaseConfig):
        self.config = config
        self.events: deque = deque(maxlen=1000)
        self._lock = threading.Lock()

    def log_event(self, event_type: str, message: str,
                 level: str = "INFO", metadata: dict[str, Any] | None = None) -> None:
        """Log an event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
            "level": level,
            "metadata": metadata or {}
        }

        with self._lock:
            self.events.append(event)

        # Also log to standard logger
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(f"[{event_type}] {message}")

    def get_recent_events(self, count: int = 100) -> list[dict[str, Any]]:
        """Get recent events."""
        with self._lock:
            return list(self.events)[-count:]

    def get_events_by_type(self, event_type: str) -> list[dict[str, Any]]:
        """Get events of a specific type."""
        with self._lock:
            return [e for e in self.events if e["type"] == event_type]


class PerformanceMonitor:
    """Monitors and analyzes system performance."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector

    def get_search_performance_report(self) -> dict[str, Any]:
        """Generate search performance report."""
        search_requests = self.metrics.get_metric("kb.search.requests")
        search_latency = self.metrics.get_metric("kb.search.latency")
        search_errors = self.metrics.get_metric("kb.search.errors")

        report = {
            "total_searches": search_requests.get_stats()["count"] if search_requests else 0,
            "avg_latency": search_latency.get_stats()["avg"] if search_latency else 0,
            "error_rate": 0
        }

        if search_requests and search_errors:
            total_searches = search_requests.get_stats()["count"]
            total_errors = search_errors.get_stats()["count"]
            report["error_rate"] = (total_errors / total_searches * 100) if total_searches > 0 else 0

        return report

    def get_generation_performance_report(self) -> dict[str, Any]:
        """Generate AI generation performance report."""
        gen_requests = self.metrics.get_metric("kb.generation.requests")
        gen_latency = self.metrics.get_metric("kb.generation.latency")
        gen_tokens = self.metrics.get_metric("kb.generation.tokens")
        gen_errors = self.metrics.get_metric("kb.generation.errors")

        report = {
            "total_generations": gen_requests.get_stats()["count"] if gen_requests else 0,
            "avg_latency": gen_latency.get_stats()["avg"] if gen_latency else 0,
            "total_tokens": gen_tokens.get_stats()["sum"] if gen_tokens else 0,
            "error_rate": 0
        }

        if gen_requests and gen_errors:
            total_gen = gen_requests.get_stats()["count"]
            total_errors = gen_errors.get_stats()["count"]
            report["error_rate"] = (total_errors / total_gen * 100) if total_gen > 0 else 0

        return report

    def get_system_health_report(self) -> dict[str, Any]:
        """Generate system health report."""
        cpu_metric = self.metrics.get_metric("kb.system.cpu_percent")
        memory_metric = self.metrics.get_metric("kb.system.memory_percent")
        disk_metric = self.metrics.get_metric("kb.system.disk_usage")

        return {
            "cpu_usage_percent": cpu_metric.get_stats()["latest"] if cpu_metric else 0,
            "memory_usage_percent": memory_metric.get_stats()["latest"] if memory_metric else 0,
            "disk_usage_percent": disk_metric.get_stats()["latest"] if disk_metric else 0,
            "status": "healthy"  # Could implement more complex health checks
        }


class AnalyticsDashboard:
    """Analytics dashboard for insights and reporting."""

    def __init__(self, metrics_collector: MetricsCollector,
                 event_logger: EventLogger, performance_monitor: PerformanceMonitor):
        self.metrics = metrics_collector
        self.events = event_logger
        self.performance = performance_monitor

    def get_dashboard_data(self) -> dict[str, Any]:
        """Get comprehensive dashboard data."""
        return {
            "timestamp": datetime.now().isoformat(),
            "search_performance": self.performance.get_search_performance_report(),
            "generation_performance": self.performance.get_generation_performance_report(),
            "system_health": self.performance.get_system_health_report(),
            "recent_events": self.events.get_recent_events(10),
            "metrics_summary": self.metrics.get_all_metrics()
        }

    def get_usage_trends(self, days: int = 7) -> dict[str, Any]:
        """Get usage trends over time."""
        trends = {
            "search_requests": self.metrics.get_metric_history("kb.search.requests", days * 24),
            "generation_requests": self.metrics.get_metric_history("kb.generation.requests", days * 24),
            "cpu_usage": self.metrics.get_metric_history("kb.system.cpu_percent", days * 24),
            "memory_usage": self.metrics.get_metric_history("kb.system.memory_percent", days * 24)
        }

        return trends

    def generate_report(self, report_type: str = "daily") -> dict[str, Any]:
        """Generate a comprehensive report."""
        if report_type == "daily":
            hours = 24
        elif report_type == "weekly":
            hours = 168
        else:
            hours = 24

        return {
            "report_type": report_type,
            "period_hours": hours,
            "generated_at": datetime.now().isoformat(),
            "dashboard_data": self.get_dashboard_data(),
            "usage_trends": self.get_usage_trends(hours // 24 if hours > 24 else 1),
            "system_info": {
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total
            }
        }


class MonitoringSystem:
    """Main monitoring system that coordinates all monitoring components."""

    def __init__(self, config: KnowledgeBaseConfig):
        self.config = config

        # Initialize components
        self.metrics = MetricsCollector(config)
        self.events = EventLogger(config)
        self.performance = PerformanceMonitor(self.metrics)
        self.analytics = AnalyticsDashboard(self.metrics, self.events, self.performance)

        logger.info("Monitoring system initialized")

    def track_search_request(self, query: str, results_count: int,
                           latency: float, user_id: str = "") -> None:
        """Track a search request."""
        self.metrics.record_metric("kb.search.requests", 1, {"user_id": user_id})
        self.metrics.record_metric("kb.search.latency", latency, {"user_id": user_id})

        self.events.log_event(
            "search_request",
            f"Search executed: '{query}' -> {results_count} results ({latency:.2f}s)",
            metadata={
                "query": query,
                "results_count": results_count,
                "latency": latency,
                "user_id": user_id
            }
        )

    def track_generation_request(self, query: str, tokens_used: int,
                               latency: float, user_id: str = "") -> None:
        """Track a generation request."""
        self.metrics.record_metric("kb.generation.requests", 1, {"user_id": user_id})
        self.metrics.record_metric("kb.generation.latency", latency, {"user_id": user_id})
        self.metrics.record_metric("kb.generation.tokens", tokens_used, {"user_id": user_id})

        self.events.log_event(
            "generation_request",
            f"AI generation: {tokens_used} tokens ({latency:.2f}s)",
            metadata={
                "query": query,
                "tokens_used": tokens_used,
                "latency": latency,
                "user_id": user_id
            }
        )

    def track_ingestion(self, document_count: int, chunk_count: int,
                       user_id: str = "") -> None:
        """Track document ingestion."""
        self.metrics.record_metric("kb.ingestion.documents", document_count, {"user_id": user_id})
        self.metrics.record_metric("kb.ingestion.chunks", chunk_count, {"user_id": user_id})

        self.events.log_event(
            "document_ingestion",
            f"Documents ingested: {document_count} docs, {chunk_count} chunks",
            metadata={
                "document_count": document_count,
                "chunk_count": chunk_count,
                "user_id": user_id
            }
        )

    def track_error(self, component: str, error_type: str, message: str) -> None:
        """Track an error."""
        metric_name = f"kb.{component}.errors"
        self.metrics.record_metric(metric_name, 1, {"error_type": error_type})

        self.events.log_event(
            "error",
            f"{component.upper()} error: {message}",
            level="ERROR",
            metadata={
                "component": component,
                "error_type": error_type,
                "message": message
            }
        )

    def get_health_status(self) -> dict[str, Any]:
        """Get overall system health status."""
        health_data = self.analytics.get_dashboard_data()

        # Determine health status based on metrics
        cpu_usage = health_data["system_health"]["cpu_usage_percent"]
        memory_usage = health_data["system_health"]["memory_usage_percent"]
        error_rate = health_data["search_performance"]["error_rate"]

        status = "healthy"
        issues = []

        if cpu_usage > 90:
            status = "critical"
            issues.append("High CPU usage")
        elif cpu_usage > 70:
            status = "warning"
            issues.append("Elevated CPU usage")

        if memory_usage > 90:
            status = "critical"
            issues.append("High memory usage")
        elif memory_usage > 80:
            status = "warning"
            issues.append("Elevated memory usage")

        if error_rate > 10:
            status = "warning"
            issues.append("High error rate")

        return {
            "status": status,
            "issues": issues,
            "metrics": health_data
        }

    def export_metrics(self, filepath: str) -> None:
        """Export all metrics to a JSON file."""
        data = {
            "exported_at": datetime.now().isoformat(),
            "metrics": self.metrics.get_all_metrics(),
            "events": self.events.get_recent_events(1000),
            "dashboard": self.analytics.get_dashboard_data()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Metrics exported to {filepath}")
