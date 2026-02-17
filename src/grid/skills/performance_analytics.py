"""
Advanced skills performance analytics and monitoring.

Provides comprehensive performance tracking, metrics collection,
anomaly detection, and performance optimization recommendations for skills.
Includes real-time monitoring, historical analysis, and predictive analytics.
"""

from __future__ import annotations

import asyncio
import json
import logging
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class MetricType(StrEnum):
    """Performance metric types."""

    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    SUCCESS_RATE = "success_rate"
    RESOURCE_EFFICIENCY = "resource_efficiency"


class AlertLevel(StrEnum):
    """Performance alert levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Individual performance metric."""

    metric_id: str
    skill_id: str
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime
    context: dict[str, Any]
    tags: set[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "metric_id": self.metric_id,
            "skill_id": self.skill_id,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "tags": list(self.tags),
        }


@dataclass
class PerformanceAlert:
    """Performance alert."""

    alert_id: str
    skill_id: str
    metric_type: MetricType
    level: AlertLevel
    message: str
    threshold_value: float
    actual_value: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "alert_id": self.alert_id,
            "skill_id": self.skill_id,
            "metric_type": self.metric_type.value,
            "level": self.level.value,
            "message": self.message,
            "threshold_value": self.threshold_value,
            "actual_value": self.actual_value,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


@dataclass
class PerformanceReport:
    """Performance analysis report."""

    report_id: str
    skill_id: str
    period_start: datetime
    period_end: datetime
    metrics_summary: dict[str, Any]
    trends: dict[str, Any]
    anomalies: list[dict[str, Any]]
    recommendations: list[str]
    performance_score: float
    generated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "report_id": self.report_id,
            "skill_id": self.skill_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "metrics_summary": self.metrics_summary,
            "trends": self.trends,
            "anomalies": self.anomalies,
            "recommendations": self.recommendations,
            "performance_score": self.performance_score,
            "generated_at": self.generated_at.isoformat(),
        }


class SkillsPerformanceAnalytics:
    """
    Advanced performance analytics for skills.

    Features:
    - Real-time metrics collection
    - Historical performance analysis
    - Anomaly detection
    - Performance optimization recommendations
    - Trend analysis
    - Alert management
    - Predictive analytics
    - Benchmarking
    """

    def __init__(self, storage_path: Path | None = None):
        """
        Initialize performance analytics.

        Args:
            storage_path: Path for analytics storage
        """
        self.storage_path = storage_path or Path("./data/performance_analytics")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Metrics storage
        self.metrics_path = self.storage_path / "metrics"
        self.metrics_path.mkdir(exist_ok=True)

        # Alerts storage
        self.alerts_path = self.storage_path / "alerts"
        self.alerts_path.mkdir(exist_ok=True)

        # Reports storage
        self.reports_path = self.storage_path / "reports"
        self.reports_path.mkdir(exist_ok=True)

        # In-memory metrics cache
        self._metrics_cache: dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._alerts_cache: list[PerformanceAlert] = []

        # Performance thresholds
        self._thresholds: dict[tuple[str, MetricType], tuple[float, AlertLevel]] = {}
        self._load_thresholds()

        # Background monitoring
        self._monitoring_task: asyncio.Task | None = None
        self._monitoring_active = False

        logger.info(f"SkillsPerformanceAnalytics initialized at {self.storage_path}")

    def record_metric(
        self,
        skill_id: str,
        metric_type: MetricType,
        value: float,
        unit: str,
        context: dict[str, Any] | None = None,
        tags: set[str] | None = None,
    ) -> str:
        """
        Record a performance metric.

        Args:
            skill_id: Skill identifier
            metric_type: Type of metric
            value: Metric value
            unit: Unit of measurement
            context: Additional context
            tags: Metric tags

        Returns:
            Metric ID
        """
        metric_id = str(uuid4())

        metric = PerformanceMetric(
            metric_id=metric_id,
            skill_id=skill_id,
            metric_type=metric_type,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            context=context or {},
            tags=tags or set(),
        )

        # Store in cache
        cache_key = f"{skill_id}:{metric_type.value}"
        self._metrics_cache[cache_key].append(metric)

        # Check thresholds and generate alerts
        self._check_thresholds(metric)

        # Persist metric
        self._persist_metric(metric)

        return metric_id

    def get_metrics(
        self,
        skill_id: str,
        metric_type: MetricType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
    ) -> list[PerformanceMetric]:
        """
        Get performance metrics.

        Args:
            skill_id: Skill identifier
            metric_type: Filter by metric type
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of metrics

        Returns:
            List of metrics
        """
        metrics = []

        # Get from cache first
        cache_keys = [f"{skill_id}:{mt.value}" for mt in MetricType if metric_type is None or mt == metric_type]

        for cache_key in cache_keys:
            if cache_key in self._metrics_cache:
                for metric in self._metrics_cache[cache_key]:
                    if start_time and metric.timestamp < start_time:
                        continue
                    if end_time and metric.timestamp > end_time:
                        continue
                    metrics.append(metric)

        # Sort by timestamp (newest first)
        metrics.sort(key=lambda m: m.timestamp, reverse=True)

        return metrics[:limit]

    def get_performance_summary(
        self,
        skill_id: str,
        period_hours: int = 24,
    ) -> dict[str, Any]:
        """
        Get performance summary for a skill.

        Args:
            skill_id: Skill identifier
            period_hours: Analysis period in hours

        Returns:
            Performance summary
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=period_hours)

        summary = {
            "skill_id": skill_id,
            "period_start": start_time.isoformat(),
            "period_end": end_time.isoformat(),
            "metrics": {},
        }

        # Calculate statistics for each metric type
        for metric_type in MetricType:
            metrics = self.get_metrics(skill_id, metric_type, start_time, end_time)

            if not metrics:
                continue

            values = [m.value for m in metrics]

            summary["metrics"][metric_type.value] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                "latest": values[-1] if values else None,
                "trend": self._calculate_trend(values),
            }

        return summary

    def generate_performance_report(
        self,
        skill_id: str,
        period_hours: int = 24,
    ) -> PerformanceReport:
        """
        Generate comprehensive performance report.

        Args:
            skill_id: Skill identifier
            period_hours: Analysis period in hours

        Returns:
            Performance report
        """
        report_id = str(uuid4())
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=period_hours)

        # Get metrics summary
        summary = self.get_performance_summary(skill_id, period_hours)

        # Analyze trends
        trends = self._analyze_trends(skill_id, start_time, end_time)

        # Detect anomalies
        anomalies = self._detect_anomalies(skill_id, start_time, end_time)

        # Generate recommendations
        recommendations = self._generate_recommendations(summary, anomalies)

        # Calculate performance score
        performance_score = self._calculate_performance_score(summary)

        report = PerformanceReport(
            report_id=report_id,
            skill_id=skill_id,
            period_start=start_time,
            period_end=end_time,
            metrics_summary=summary,
            trends=trends,
            anomalies=anomalies,
            recommendations=recommendations,
            performance_score=performance_score,
            generated_at=datetime.now(),
        )

        # Save report
        self._save_report(report)

        return report

    def set_threshold(
        self,
        skill_id: str,
        metric_type: MetricType,
        threshold_value: float,
        alert_level: AlertLevel,
    ) -> None:
        """
        Set performance threshold for alerting.

        Args:
            skill_id: Skill identifier
            metric_type: Metric type
            threshold_value: Threshold value
            alert_level: Alert level
        """
        self._thresholds[(skill_id, metric_type)] = (threshold_value, alert_level)
        self._save_thresholds()

    def get_alerts(
        self,
        skill_id: str | None = None,
        level: AlertLevel | None = None,
        resolved: bool | None = None,
        limit: int = 100,
    ) -> list[PerformanceAlert]:
        """
        Get performance alerts.

        Args:
            skill_id: Filter by skill ID
            level: Filter by alert level
            resolved: Filter by resolved status
            limit: Maximum number of alerts

        Returns:
            List of alerts
        """
        alerts = self._alerts_cache

        if skill_id:
            alerts = [a for a in alerts if a.skill_id == skill_id]

        if level:
            alerts = [a for a in alerts if a.level == level]

        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]

        # Sort by timestamp (newest first)
        alerts.sort(key=lambda a: a.timestamp, reverse=True)

        return alerts[:limit]

    def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve a performance alert.

        Args:
            alert_id: Alert identifier

        Returns:
            True if resolved successfully
        """
        for alert in self._alerts_cache:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                self._save_alert(alert)
                return True
        return False

    def start_monitoring(self, interval_seconds: int = 60) -> None:
        """
        Start background monitoring.

        Args:
            interval_seconds: Monitoring interval
        """
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(interval_seconds))
        logger.info("Performance monitoring started")

    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        if not self._monitoring_active:
            return

        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                asyncio.get_event_loop().run_until_complete(self._monitoring_task)
            except asyncio.CancelledError:
                pass
        logger.info("Performance monitoring stopped")

    def _persist_metric(self, metric: PerformanceMetric) -> None:
        """Persist metric to storage."""
        date_dir = self.metrics_path / metric.timestamp.strftime("%Y-%m-%d")
        date_dir.mkdir(exist_ok=True)

        metric_file = date_dir / f"{metric.skill_id}_{metric.metric_type.value}.jsonl"

        with open(metric_file, "a") as f:
            f.write(json.dumps(metric.to_dict()) + "\n")

    def _check_thresholds(self, metric: PerformanceMetric) -> None:
        """Check metric against thresholds and generate alerts."""
        threshold_key = (metric.skill_id, metric.metric_type)

        if threshold_key not in self._thresholds:
            return

        threshold_value, alert_level = self._thresholds[threshold_key]

        # Check if threshold is exceeded
        if self._is_threshold_exceeded(metric.metric_type, metric.value, threshold_value):
            alert = PerformanceAlert(
                alert_id=str(uuid4()),
                skill_id=metric.skill_id,
                metric_type=metric.metric_type,
                level=alert_level,
                message=f"{metric.metric_type.value} threshold exceeded: {metric.value} {metric.unit} > {threshold_value} {metric.unit}",
                threshold_value=threshold_value,
                actual_value=metric.value,
                timestamp=metric.timestamp,
            )

            self._alerts_cache.append(alert)
            self._save_alert(alert)

            logger.warning(f"Performance alert generated: {alert.message}")

    def _is_threshold_exceeded(self, metric_type: MetricType, value: float, threshold: float) -> bool:
        """Check if metric value exceeds threshold."""
        # Different metrics have different threshold logic
        if metric_type in [MetricType.EXECUTION_TIME, MetricType.LATENCY, MetricType.ERROR_RATE]:
            return value > threshold
        elif metric_type in [MetricType.SUCCESS_RATE, MetricType.THROUGHPUT]:
            return value < threshold
        else:
            return value > threshold

    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend direction from values."""
        if len(values) < 2:
            return "stable"

        # Simple linear regression
        n = len(values)
        x = list(range(n))

        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"

    def _analyze_trends(self, skill_id: str, start_time: datetime, end_time: datetime) -> dict[str, Any]:
        """Analyze performance trends."""
        trends = {}

        for metric_type in MetricType:
            metrics = self.get_metrics(skill_id, metric_type, start_time, end_time)

            if len(metrics) < 2:
                continue

            values = [m.value for m in metrics]
            timestamps = [m.timestamp.timestamp() for m in metrics]

            # Calculate trend
            trend_direction = self._calculate_trend(values)

            # Calculate trend strength (correlation coefficient)
            if len(values) > 1:
                correlation = self._calculate_correlation(timestamps, values)
            else:
                correlation = 0.0

            trends[metric_type.value] = {
                "direction": trend_direction,
                "strength": abs(correlation),
                "correlation": correlation,
            }

        return trends

    def _detect_anomalies(self, skill_id: str, start_time: datetime, end_time: datetime) -> list[dict[str, Any]]:
        """Detect performance anomalies."""
        anomalies = []

        for metric_type in MetricType:
            metrics = self.get_metrics(skill_id, metric_type, start_time, end_time)

            if len(metrics) < 10:  # Need sufficient data for anomaly detection
                continue

            values = [m.value for m in metrics]

            # Detect outliers using IQR method
            q1 = statistics.quantiles(values, n=4)[0]
            q3 = statistics.quantiles(values, n=4)[2]
            iqr = q3 - q1

            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            anomalies.extend(
                {
                    "metric_type": metric_type.value,
                    "timestamp": metric.timestamp.isoformat(),
                    "value": metric.value,
                    "expected_range": [lower_bound, upper_bound],
                    "severity": "high" if abs(metric.value - statistics.mean(values)) > 2 * iqr else "medium",
                }
                for metric in metrics
                if metric.value < lower_bound or metric.value > upper_bound
            )

        return anomalies

    def _generate_recommendations(self, summary: dict[str, Any], anomalies: list[dict[str, Any]]) -> list[str]:
        """Generate performance optimization recommendations."""
        recommendations = []

        # Analyze metrics for recommendations
        for metric_name, metric_data in summary.get("metrics", {}).items():
            if metric_name == MetricType.EXECUTION_TIME.value:
                if metric_data["mean"] > 5.0:  # 5 seconds
                    recommendations.append(
                        f"Consider optimizing skill execution time (current avg: {metric_data['mean']:.2f}s)"
                    )

            elif metric_name == MetricType.ERROR_RATE.value:
                if metric_data["mean"] > 0.1:  # 10% error rate
                    recommendations.append("High error rate detected, review error handling and input validation")

            elif metric_name == MetricType.MEMORY_USAGE.value:
                if metric_data["mean"] > 512:  # 512MB
                    recommendations.append("High memory usage detected, consider memory optimization")

        # Anomaly-based recommendations
        if len(anomalies) > 5:
            recommendations.append("Multiple performance anomalies detected, consider comprehensive performance review")

        # Trend-based recommendations
        for metric_name, metric_data in summary.get("metrics", {}).items():
            if metric_data.get("trend") == "increasing" and metric_name in [
                MetricType.EXECUTION_TIME.value,
                MetricType.ERROR_RATE.value,
                MetricType.MEMORY_USAGE.value,
            ]:
                recommendations.append(f"Concerning upward trend in {metric_name}, investigate root cause")

        return recommendations

    def _calculate_performance_score(self, summary: dict[str, Any]) -> float:
        """Calculate overall performance score."""
        score = 100.0

        # Deduct points for poor metrics
        metrics = summary.get("metrics", {})

        # Execution time penalty
        if MetricType.EXECUTION_TIME.value in metrics:
            exec_time = metrics[MetricType.EXECUTION_TIME.value]["mean"]
            if exec_time > 10.0:
                score -= 30
            elif exec_time > 5.0:
                score -= 15
            elif exec_time > 2.0:
                score -= 5

        # Error rate penalty
        if MetricType.ERROR_RATE.value in metrics:
            error_rate = metrics[MetricType.ERROR_RATE.value]["mean"]
            if error_rate > 0.2:  # 20%
                score -= 40
            elif error_rate > 0.1:  # 10%
                score -= 20
            elif error_rate > 0.05:  # 5%
                score -= 10

        # Success rate bonus/penalty
        if MetricType.SUCCESS_RATE.value in metrics:
            success_rate = metrics[MetricType.SUCCESS_RATE.value]["mean"]
            if success_rate > 0.95:  # 95%
                score += 10
            elif success_rate < 0.9:  # 90%
                score -= 15
            elif success_rate < 0.8:  # 80%
                score -= 30

        return max(0.0, min(100.0, score))

    def _calculate_correlation(self, x: list[float], y: list[float]) -> float:
        """Calculate correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        x_std = statistics.stdev(x) if len(x) > 1 else 0
        y_std = statistics.stdev(y) if len(y) > 1 else 0

        if x_std == 0 or y_std == 0:
            return 0.0

        return numerator / (n * x_std * y_std)

    async def _monitoring_loop(self, interval_seconds: int) -> None:
        """Background monitoring loop."""
        while self._monitoring_active:
            try:
                # Perform monitoring tasks
                await self._perform_monitoring_checks()

                # Sleep until next check
                await asyncio.sleep(interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(interval_seconds)

    async def _perform_monitoring_checks(self) -> None:
        """Perform periodic monitoring checks."""
        # This would include automated health checks,
        # performance validation, and maintenance tasks

        # Clean old metrics from cache
        cutoff_time = datetime.now() - timedelta(hours=24)

        for metrics_deque in self._metrics_cache.values():
            while metrics_deque and metrics_deque[0].timestamp < cutoff_time:
                metrics_deque.popleft()

    def _save_report(self, report: PerformanceReport) -> None:
        """Save performance report."""
        report_file = self.reports_path / f"{report.report_id}.json"
        report_file.write_text(json.dumps(report.to_dict(), indent=2))

    def _save_alert(self, alert: PerformanceAlert) -> None:
        """Save performance alert."""
        alert_file = self.alerts_path / f"{alert.alert_id}.json"
        alert_file.write_text(json.dumps(alert.to_dict(), indent=2))

    def _load_thresholds(self) -> None:
        """Load performance thresholds."""
        thresholds_file = self.storage_path / "thresholds.json"

        if thresholds_file.exists():
            try:
                data = json.loads(thresholds_file.read_text())
                for key_str, (value, level_str) in data.items():
                    skill_id, metric_type_str = key_str.split(":")
                    metric_type = MetricType(metric_type_str)
                    alert_level = AlertLevel(level_str)
                    self._thresholds[(skill_id, metric_type)] = (value, alert_level)
            except Exception as e:
                logger.error(f"Failed to load thresholds: {e}")

    def _save_thresholds(self) -> None:
        """Save performance thresholds."""
        thresholds_file = self.storage_path / "thresholds.json"

        try:
            data = {}
            for (skill_id, metric_type), (value, alert_level) in self._thresholds.items():
                key_str = f"{skill_id}:{metric_type.value}"
                data[key_str] = [value, alert_level.value]

            thresholds_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save thresholds: {e}")


# Global analytics instance
_global_analytics: SkillsPerformanceAnalytics | None = None


def get_skills_performance_analytics() -> SkillsPerformanceAnalytics:
    """Get or create global skills performance analytics instance."""
    global _global_analytics
    if _global_analytics is None:
        _global_analytics = SkillsPerformanceAnalytics()
    return _global_analytics


def set_skills_performance_analytics(analytics: SkillsPerformanceAnalytics) -> None:
    """Set global skills performance analytics instance."""
    global _global_analytics
    _global_analytics = analytics
