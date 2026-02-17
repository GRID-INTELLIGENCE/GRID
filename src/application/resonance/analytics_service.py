"""
Resonance Analytics Service - Automated Insight Engine.

Transforms raw telemetry data into actionable intelligence through:
- Real-time spike detection (Impact > 0.9)
- Modality balance monitoring
- Threshold-based alerting
- Historical pattern analysis
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class AlertSeverity(StrEnum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class InsightType(StrEnum):
    """Types of automated insights."""

    SPIKE_DETECTED = "spike_detected"
    IMBALANCE = "imbalance"
    EFFICIENCY_DROP = "efficiency_drop"
    ANOMALY = "anomaly"
    PATTERN = "pattern"


@dataclass
class Alert:
    """Represents an alert triggered by the analytics engine."""

    id: str
    severity: AlertSeverity
    insight_type: InsightType
    message: str
    timestamp: datetime
    data: dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None


@dataclass
class SpikeSummary:
    """Summary of high-impact spike events."""

    window_start: datetime
    window_end: datetime
    spike_count: int
    avg_impact: float
    max_impact: float
    event_types: dict[str, int]
    density_per_minute: float


@dataclass
class BalanceReport:
    """Report on modality balance (event type distribution)."""

    timestamp: datetime
    total_events: int
    type_distribution: dict[str, float]  # event_type -> percentage
    imbalance_ratio: float  # 0.0 (perfect) to 1.0 (completely imbalanced)
    dominant_type: str | None
    is_healthy: bool  # True if within 60/40 threshold


@dataclass
class EfficiencyMetrics:
    """Metrics for system efficiency."""

    timestamp: datetime
    total_events: int
    high_impact_events: int  # Impact > 0.7
    low_impact_events: int  # Impact < 0.3
    efficiency_score: float  # 0.0 to 1.0
    cost_per_meaningful_event: float
    processing_latency_ms: float


@dataclass
class AnalyticsInsight:
    """A generated insight from the analytics engine."""

    id: str
    insight_type: InsightType
    title: str
    description: str
    severity: AlertSeverity
    timestamp: datetime
    metrics: dict[str, Any]
    recommendations: list[str]
    auto_actionable: bool = False
    action_taken: bool = False


class AnalyticsService:
    """
    Automated Analytics Service for Resonance Telemetry.

    Implements the three core investigative queries:
    1. Spike Detection: Monitor impact > 0.9 events in real-time
    2. Balance Monitoring: Track event type ratios
    3. Efficiency Analysis: Compute cost per meaningful event
    """

    # Configuration thresholds
    SPIKE_THRESHOLD = 0.9
    SPIKE_DENSITY_ALERT_THRESHOLD = 5  # spikes per minute
    IMBALANCE_THRESHOLD = 0.8  # 80/20 ratio triggers alert
    EFFICIENCY_LOW_THRESHOLD = 0.3
    WINDOW_SIZE_SECONDS = 60  # Analysis window

    def __init__(
        self,
        alert_callback: Callable[[Alert], None] | None = None,
        insight_callback: Callable[[AnalyticsInsight], None] | None = None,
    ):
        """
        Initialize the Analytics Service.

        Args:
            alert_callback: Optional callback for immediate alerts
            insight_callback: Optional callback for generated insights
        """
        self._alert_callback = alert_callback
        self._insight_callback = insight_callback

        # Real-time event buffers (circular buffers for efficiency)
        self._event_buffer: deque[dict[str, Any]] = deque(maxlen=10000)
        self._spike_buffer: deque[dict[str, Any]] = deque(maxlen=1000)

        # State tracking
        self._alerts: list[Alert] = []
        self._insights: list[AnalyticsInsight] = []
        self._spike_summaries: list[SpikeSummary] = []
        self._balance_reports: list[BalanceReport] = []
        self._efficiency_metrics: list[EfficiencyMetrics] = []

        # Running statistics
        self._event_type_counts: dict[str, int] = {}
        self._total_events_processed: int = 0
        self._high_impact_count: int = 0

        # Background task tracking
        self._monitoring_task: asyncio.Task | None = None
        self._is_running: bool = False

        # Alert ID counter
        self._alert_counter: int = 0
        self._insight_counter: int = 0

    async def start(self) -> None:
        """Start the analytics monitoring loop."""
        if self._is_running:
            logger.warning("AnalyticsService already running")
            return

        self._is_running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("AnalyticsService started")

    async def stop(self) -> None:
        """Stop the analytics monitoring loop."""
        self._is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("AnalyticsService stopped")

    async def ingest_event(self, event: dict[str, Any]) -> None:
        """
        Ingest a single event for analysis.

        Args:
            event: Event dict with 'type', 'impact', 'timestamp', 'data' keys
        """
        # Add timestamp if missing
        if "timestamp" not in event:
            event["timestamp"] = datetime.now(UTC).isoformat()

        # Buffer the event
        self._event_buffer.append(event)
        self._total_events_processed += 1

        # Track event type distribution
        event_type = event.get("type", "UNKNOWN")
        self._event_type_counts[event_type] = self._event_type_counts.get(event_type, 0) + 1

        # Real-time spike detection
        impact = event.get("impact", 0.5)
        if impact >= self.SPIKE_THRESHOLD:
            self._spike_buffer.append(event)
            self._high_impact_count += 1
            await self._handle_spike(event)

        logger.debug(f"Ingested event: {event_type} (impact: {impact:.2f})")

    async def ingest_batch(self, events: list[dict[str, Any]]) -> None:
        """
        Ingest a batch of events for analysis.

        Args:
            events: List of event dicts
        """
        for event in events:
            await self.ingest_event(event)

    async def _handle_spike(self, event: dict[str, Any]) -> None:
        """Handle a detected spike event (impact >= 0.9)."""
        # Check spike density in the last window
        window_start = datetime.now(UTC) - timedelta(seconds=self.WINDOW_SIZE_SECONDS)
        recent_spikes = [e for e in self._spike_buffer if self._parse_timestamp(e.get("timestamp")) >= window_start]

        density = len(recent_spikes) / (self.WINDOW_SIZE_SECONDS / 60)  # spikes per minute

        if density >= self.SPIKE_DENSITY_ALERT_THRESHOLD:
            alert = await self._create_alert(
                severity=AlertSeverity.CRITICAL,
                insight_type=InsightType.SPIKE_DETECTED,
                message=f"High spike density detected: {density:.1f} spikes/minute (threshold: {self.SPIKE_DENSITY_ALERT_THRESHOLD})",
                data={
                    "density": density,
                    "spike_count": len(recent_spikes),
                    "window_seconds": self.WINDOW_SIZE_SECONDS,
                    "latest_spike": event,
                },
            )

            if self._alert_callback:
                self._alert_callback(alert)

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop for periodic analysis."""
        while self._is_running:
            try:
                # Generate periodic reports
                await self._generate_spike_summary()
                await self._generate_balance_report()
                await self._generate_efficiency_metrics()

                # Check for insights
                await self._analyze_patterns()

                # Sleep until next analysis window
                await asyncio.sleep(self.WINDOW_SIZE_SECONDS)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Analytics monitoring error: {e}")
                await asyncio.sleep(5)  # Backoff on error

    async def _generate_spike_summary(self) -> SpikeSummary:
        """Generate a summary of recent spike events."""
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=self.WINDOW_SIZE_SECONDS)

        recent_spikes = [e for e in self._spike_buffer if self._parse_timestamp(e.get("timestamp")) >= window_start]

        if not recent_spikes:
            summary = SpikeSummary(
                window_start=window_start,
                window_end=now,
                spike_count=0,
                avg_impact=0.0,
                max_impact=0.0,
                event_types={},
                density_per_minute=0.0,
            )
        else:
            impacts = [e.get("impact", 0.9) for e in recent_spikes]
            type_counts: dict[str, int] = {}
            for e in recent_spikes:
                t = e.get("type", "UNKNOWN")
                type_counts[t] = type_counts.get(t, 0) + 1

            summary = SpikeSummary(
                window_start=window_start,
                window_end=now,
                spike_count=len(recent_spikes),
                avg_impact=sum(impacts) / len(impacts),
                max_impact=max(impacts),
                event_types=type_counts,
                density_per_minute=len(recent_spikes) / (self.WINDOW_SIZE_SECONDS / 60),
            )

        self._spike_summaries.append(summary)

        # Keep only last 100 summaries
        if len(self._spike_summaries) > 100:
            self._spike_summaries = self._spike_summaries[-100:]

        logger.debug(f"Spike summary: {summary.spike_count} spikes, density: {summary.density_per_minute:.1f}/min")
        return summary

    async def _generate_balance_report(self) -> BalanceReport:
        """Generate a modality balance report."""
        now = datetime.now(UTC)
        total = sum(self._event_type_counts.values())

        if total == 0:
            report = BalanceReport(
                timestamp=now,
                total_events=0,
                type_distribution={},
                imbalance_ratio=0.0,
                dominant_type=None,
                is_healthy=True,
            )
        else:
            distribution = {k: v / total for k, v in self._event_type_counts.items()}
            max_ratio = max(distribution.values()) if distribution else 0.0
            dominant = max(distribution.keys(), key=lambda k: distribution[k]) if distribution else None

            # Imbalance ratio: how far from uniform distribution
            # 0.0 = perfect balance, 1.0 = completely imbalanced
            num_types = len(distribution)
            expected_ratio = 1.0 / num_types if num_types > 0 else 0.0
            variance = (
                sum((v - expected_ratio) ** 2 for v in distribution.values()) / num_types if num_types > 0 else 0.0
            )
            imbalance = min(1.0, variance * num_types * 4)  # Scaled variance

            is_healthy = max_ratio <= self.IMBALANCE_THRESHOLD

            report = BalanceReport(
                timestamp=now,
                total_events=total,
                type_distribution=distribution,
                imbalance_ratio=imbalance,
                dominant_type=dominant,
                is_healthy=is_healthy,
            )

            # Alert if imbalanced
            if not is_healthy:
                alert = await self._create_alert(
                    severity=AlertSeverity.WARNING,
                    insight_type=InsightType.IMBALANCE,
                    message=f"Modality imbalance detected: {dominant} at {max_ratio * 100:.1f}% (threshold: {self.IMBALANCE_THRESHOLD * 100:.0f}%)",
                    data={
                        "distribution": distribution,
                        "dominant_type": dominant,
                        "dominant_ratio": max_ratio,
                    },
                )
                if self._alert_callback:
                    self._alert_callback(alert)

        self._balance_reports.append(report)

        # Keep only last 100 reports
        if len(self._balance_reports) > 100:
            self._balance_reports = self._balance_reports[-100:]

        logger.debug(f"Balance report: {report.total_events} events, imbalance: {report.imbalance_ratio:.2f}")
        return report

    async def _generate_efficiency_metrics(self) -> EfficiencyMetrics:
        """Generate efficiency metrics."""
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=self.WINDOW_SIZE_SECONDS)

        recent_events = [e for e in self._event_buffer if self._parse_timestamp(e.get("timestamp")) >= window_start]

        total = len(recent_events)
        high_impact = sum(1 for e in recent_events if e.get("impact", 0.5) > 0.7)
        low_impact = sum(1 for e in recent_events if e.get("impact", 0.5) < 0.3)

        # Efficiency = ratio of meaningful (high-impact) events to total
        efficiency = high_impact / total if total > 0 else 0.0

        # Cost per meaningful event (simulated - in real system, use actual compute costs)
        base_cost_per_event = 0.001  # $0.001 per event
        cost_per_meaningful = (base_cost_per_event * total) / high_impact if high_impact > 0 else float("inf")

        # Simulated latency (in real system, measure actual processing time)
        latency_ms = 50.0 + (total * 0.1)  # Base + per-event overhead

        metrics = EfficiencyMetrics(
            timestamp=now,
            total_events=total,
            high_impact_events=high_impact,
            low_impact_events=low_impact,
            efficiency_score=efficiency,
            cost_per_meaningful_event=cost_per_meaningful,
            processing_latency_ms=latency_ms,
        )

        self._efficiency_metrics.append(metrics)

        # Alert on low efficiency
        if efficiency < self.EFFICIENCY_LOW_THRESHOLD and total > 10:
            alert = await self._create_alert(
                severity=AlertSeverity.WARNING,
                insight_type=InsightType.EFFICIENCY_DROP,
                message=f"Low efficiency detected: {efficiency * 100:.1f}% (threshold: {self.EFFICIENCY_LOW_THRESHOLD * 100:.0f}%)",
                data={
                    "efficiency": efficiency,
                    "total_events": total,
                    "high_impact_events": high_impact,
                },
            )
            if self._alert_callback:
                self._alert_callback(alert)

        # Keep only last 100 metrics
        if len(self._efficiency_metrics) > 100:
            self._efficiency_metrics = self._efficiency_metrics[-100:]

        logger.debug(
            f"Efficiency metrics: {efficiency * 100:.1f}% efficiency, cost: ${cost_per_meaningful:.4f}/meaningful event"
        )
        return metrics

    async def _analyze_patterns(self) -> None:
        """Analyze patterns across all metrics to generate insights."""
        # Check for sustained spike patterns
        if len(self._spike_summaries) >= 3:
            recent = self._spike_summaries[-3:]
            avg_density = sum(s.density_per_minute for s in recent) / 3
            if avg_density > self.SPIKE_DENSITY_ALERT_THRESHOLD * 0.7:
                insight = await self._create_insight(
                    insight_type=InsightType.PATTERN,
                    title="Sustained High Spike Activity",
                    description=f"Spike density has remained elevated at {avg_density:.1f}/min over the last 3 windows",
                    severity=AlertSeverity.WARNING,
                    metrics={"avg_density": avg_density, "windows": 3},
                    recommendations=[
                        "Consider increasing attack_time parameter to smooth response",
                        "Review event sources for abnormal activity",
                        "Enable adaptive rate limiting",
                    ],
                )
                if self._insight_callback:
                    self._insight_callback(insight)

    async def _create_alert(
        self,
        severity: AlertSeverity,
        insight_type: InsightType,
        message: str,
        data: dict[str, Any],
    ) -> Alert:
        """Create and store an alert."""
        self._alert_counter += 1
        alert = Alert(
            id=f"ALT-{self._alert_counter:06d}",
            severity=severity,
            insight_type=insight_type,
            message=message,
            timestamp=datetime.now(UTC),
            data=data,
        )
        self._alerts.append(alert)

        # Keep only last 1000 alerts
        if len(self._alerts) > 1000:
            self._alerts = self._alerts[-1000:]

        logger.info(f"Alert created: [{severity.value.upper()}] {message}")
        return alert

    async def _create_insight(
        self,
        insight_type: InsightType,
        title: str,
        description: str,
        severity: AlertSeverity,
        metrics: dict[str, Any],
        recommendations: list[str],
        auto_actionable: bool = False,
    ) -> AnalyticsInsight:
        """Create and store an insight."""
        self._insight_counter += 1
        insight = AnalyticsInsight(
            id=f"INS-{self._insight_counter:06d}",
            insight_type=insight_type,
            title=title,
            description=description,
            severity=severity,
            timestamp=datetime.now(UTC),
            metrics=metrics,
            recommendations=recommendations,
            auto_actionable=auto_actionable,
        )
        self._insights.append(insight)

        # Keep only last 500 insights
        if len(self._insights) > 500:
            self._insights = self._insights[-500:]

        logger.info(f"Insight generated: {title}")
        return insight

    def _parse_timestamp(self, ts: Any) -> datetime:
        """Parse timestamp from various formats."""
        if ts is None:
            return datetime.now(UTC)
        if isinstance(ts, datetime):
            return ts if ts.tzinfo else ts.replace(tzinfo=UTC)
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
            except ValueError:
                return datetime.now(UTC)
        return datetime.now(UTC)

    # ==================== Query Methods ====================

    def get_latest_spike_summary(self) -> SpikeSummary | None:
        """Get the most recent spike summary."""
        return self._spike_summaries[-1] if self._spike_summaries else None

    def get_latest_balance_report(self) -> BalanceReport | None:
        """Get the most recent balance report."""
        return self._balance_reports[-1] if self._balance_reports else None

    def get_latest_efficiency_metrics(self) -> EfficiencyMetrics | None:
        """Get the most recent efficiency metrics."""
        return self._efficiency_metrics[-1] if self._efficiency_metrics else None

    def get_alerts(
        self,
        severity: AlertSeverity | None = None,
        acknowledged: bool | None = None,
        limit: int = 50,
    ) -> list[Alert]:
        """Get alerts with optional filtering."""
        alerts = self._alerts.copy()

        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        return alerts[-limit:]

    def get_insights(
        self,
        insight_type: InsightType | None = None,
        limit: int = 50,
    ) -> list[AnalyticsInsight]:
        """Get insights with optional filtering."""
        insights = self._insights.copy()

        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]

        return insights[-limit:]

    async def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_at = datetime.now(UTC)
                alert.acknowledged_by = user_id
                logger.info(f"Alert {alert_id} acknowledged by {user_id}")
                return True
        return False

    def get_statistics(self) -> dict[str, Any]:
        """Get overall analytics statistics."""
        return {
            "total_events_processed": self._total_events_processed,
            "high_impact_events": self._high_impact_count,
            "event_type_counts": self._event_type_counts.copy(),
            "active_alerts": len([a for a in self._alerts if not a.acknowledged]),
            "total_alerts": len(self._alerts),
            "total_insights": len(self._insights),
            "spike_summaries_count": len(self._spike_summaries),
            "balance_reports_count": len(self._balance_reports),
            "is_running": self._is_running,
        }

    # ==================== Core Query Execution ====================

    async def execute_impact_distribution_query(self) -> dict[str, Any]:
        """
        Execute Query 1: Impact Distribution.

        Returns mean impact and count per event type.
        """
        result: dict[str, dict[str, float]] = {}

        for event in self._event_buffer:
            event_type = event.get("type", "UNKNOWN")
            impact = event.get("impact", 0.5)

            if event_type not in result:
                result[event_type] = {"total_impact": 0.0, "count": 0}

            result[event_type]["total_impact"] += impact
            result[event_type]["count"] += 1

        distribution = {
            k: {
                "mean_impact": v["total_impact"] / v["count"],
                "count": int(v["count"]),
            }
            for k, v in result.items()
        }

        return {
            "query": "impact_distribution",
            "timestamp": datetime.now(UTC).isoformat(),
            "distribution": distribution,
        }

    async def execute_hot_activities_query(self, density_threshold: int = 10) -> dict[str, Any]:
        """
        Execute Query 2: Hot Activities.

        Returns activities with event density above threshold.
        """
        activity_counts: dict[str, int] = {}

        for event in self._event_buffer:
            activity_id = event.get("data", {}).get("activity_id")
            if activity_id:
                activity_counts[activity_id] = activity_counts.get(activity_id, 0) + 1

        hot_activities = {k: v for k, v in activity_counts.items() if v > density_threshold}

        return {
            "query": "hot_activities",
            "timestamp": datetime.now(UTC).isoformat(),
            "density_threshold": density_threshold,
            "hot_activities": hot_activities,
        }

    async def execute_temporal_flow_query(self, activity_id: str | None = None, window_size: int = 5) -> dict[str, Any]:
        """
        Execute Query 3: Temporal Flow with Rolling Impact.

        Returns events with rolling average impact.
        """
        events = list(self._event_buffer)
        if activity_id:
            events = [e for e in events if e.get("data", {}).get("activity_id") == activity_id]

        # Sort by timestamp
        events.sort(key=lambda e: self._parse_timestamp(e.get("timestamp")))

        # Calculate rolling impact
        flow = []
        for i, event in enumerate(events):
            window_start = max(0, i - window_size + 1)
            window_events = events[window_start : i + 1]
            rolling_avg = sum(e.get("impact", 0.5) for e in window_events) / len(window_events)

            flow.append(
                {
                    "timestamp": event.get("timestamp"),
                    "event_type": event.get("type"),
                    "impact": event.get("impact", 0.5),
                    "rolling_impact": rolling_avg,
                }
            )

        return {
            "query": "temporal_flow",
            "timestamp": datetime.now(UTC).isoformat(),
            "activity_id": activity_id,
            "window_size": window_size,
            "flow": flow[-100:],  # Last 100 entries
        }
