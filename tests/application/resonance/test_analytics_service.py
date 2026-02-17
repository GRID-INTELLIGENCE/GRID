"""
Tests for Resonance Analytics Service.

Covers:
- Event ingestion and buffering
- Real-time spike detection
- Balance monitoring
- Efficiency metrics
- Alert generation
- Core query execution
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from application.resonance.analytics_service import (
    Alert,
    AlertSeverity,
    AnalyticsService,
    BalanceReport,
    EfficiencyMetrics,
    InsightType,
    SpikeSummary,
)


@pytest.fixture
def analytics_service():
    """Create a fresh AnalyticsService instance."""
    return AnalyticsService()


@pytest.fixture
def analytics_service_with_callbacks():
    """Create analytics service with mock callbacks."""
    alert_callback = MagicMock()
    insight_callback = MagicMock()

    service = AnalyticsService(
        alert_callback=alert_callback,
        insight_callback=insight_callback,
    )

    return service, alert_callback, insight_callback


class TestEventIngestion:
    """Test event ingestion functionality."""

    @pytest.mark.asyncio
    async def test_ingest_single_event(self, analytics_service):
        """Test ingesting a single event."""
        event = {
            "type": "TEST_EVENT",
            "impact": 0.5,
            "data": {"key": "value"},
        }

        await analytics_service.ingest_event(event)

        stats = analytics_service.get_statistics()
        assert stats["total_events_processed"] == 1
        assert "TEST_EVENT" in stats["event_type_counts"]

    @pytest.mark.asyncio
    async def test_ingest_batch(self, analytics_service):
        """Test batch event ingestion."""
        events = [
            {"type": "EVENT_A", "impact": 0.3},
            {"type": "EVENT_B", "impact": 0.6},
            {"type": "EVENT_A", "impact": 0.4},
        ]

        await analytics_service.ingest_batch(events)

        stats = analytics_service.get_statistics()
        assert stats["total_events_processed"] == 3
        assert stats["event_type_counts"]["EVENT_A"] == 2
        assert stats["event_type_counts"]["EVENT_B"] == 1

    @pytest.mark.asyncio
    async def test_auto_timestamp_addition(self, analytics_service):
        """Test that missing timestamps are auto-added."""
        event = {"type": "NO_TIMESTAMP", "impact": 0.5}

        await analytics_service.ingest_event(event)

        assert "timestamp" in event


class TestSpikeDetection:
    """Test real-time spike detection."""

    @pytest.mark.asyncio
    async def test_spike_buffer_population(self, analytics_service):
        """Test that high-impact events are buffered."""
        # Add high-impact event
        await analytics_service.ingest_event(
            {
                "type": "HIGH_IMPACT",
                "impact": 0.95,
            }
        )

        stats = analytics_service.get_statistics()
        assert stats["high_impact_events"] == 1

    @pytest.mark.asyncio
    async def test_low_impact_not_spiked(self, analytics_service):
        """Test that low-impact events don't count as spikes."""
        await analytics_service.ingest_event(
            {
                "type": "LOW_IMPACT",
                "impact": 0.3,
            }
        )

        stats = analytics_service.get_statistics()
        assert stats["high_impact_events"] == 0

    @pytest.mark.asyncio
    async def test_spike_alert_triggered(self, analytics_service_with_callbacks):
        """Test that spike density triggers alerts."""
        service, alert_callback, _ = analytics_service_with_callbacks

        # Inject many spikes to trigger density alert
        for i in range(10):
            await service.ingest_event(
                {
                    "type": "SPIKE",
                    "impact": 0.95,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

        # Alert should have been triggered
        assert alert_callback.call_count >= 1

        # Check alert properties
        alert = alert_callback.call_args[0][0]
        assert isinstance(alert, Alert)
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.insight_type == InsightType.SPIKE_DETECTED


class TestBalanceMonitoring:
    """Test modality balance monitoring."""

    @pytest.mark.asyncio
    async def test_generate_balance_report(self, analytics_service):
        """Test balance report generation."""
        # Add balanced events
        for _ in range(5):
            await analytics_service.ingest_event({"type": "TYPE_A", "impact": 0.5})
            await analytics_service.ingest_event({"type": "TYPE_B", "impact": 0.5})

        report = await analytics_service._generate_balance_report()

        assert isinstance(report, BalanceReport)
        assert report.total_events == 10
        assert len(report.type_distribution) == 2
        assert report.is_healthy  # 50/50 is healthy

    @pytest.mark.asyncio
    async def test_imbalance_detected(self, analytics_service_with_callbacks):
        """Test that imbalance triggers an alert."""
        service, alert_callback, _ = analytics_service_with_callbacks

        # Create severe imbalance
        for _ in range(90):
            await service.ingest_event({"type": "DOMINANT", "impact": 0.5})
        for _ in range(10):
            await service.ingest_event({"type": "MINORITY", "impact": 0.5})

        # Generate balance report
        await service._generate_balance_report()

        # Check for imbalance alert
        assert alert_callback.call_count >= 1

        # Find the imbalance alert
        for call in alert_callback.call_args_list:
            alert = call[0][0]
            if alert.insight_type == InsightType.IMBALANCE:
                assert alert.severity == AlertSeverity.WARNING
                break


class TestEfficiencyMetrics:
    """Test efficiency analysis."""

    @pytest.mark.asyncio
    async def test_generate_efficiency_metrics(self, analytics_service):
        """Test efficiency metrics generation."""
        # Add mixed-impact events
        await analytics_service.ingest_event({"type": "HIGH", "impact": 0.8})
        await analytics_service.ingest_event({"type": "LOW", "impact": 0.2})
        await analytics_service.ingest_event({"type": "MED", "impact": 0.5})

        metrics = await analytics_service._generate_efficiency_metrics()

        assert isinstance(metrics, EfficiencyMetrics)
        assert metrics.total_events == 3
        assert metrics.high_impact_events == 1  # impact > 0.7
        assert metrics.low_impact_events == 1  # impact < 0.3
        assert 0 <= metrics.efficiency_score <= 1

    @pytest.mark.asyncio
    async def test_low_efficiency_alert(self, analytics_service_with_callbacks):
        """Test that low efficiency triggers an alert."""
        service, alert_callback, _ = analytics_service_with_callbacks

        # Add many low-impact events (low efficiency)
        for _ in range(20):
            await service.ingest_event({"type": "LOW", "impact": 0.1})

        # Generate efficiency metrics
        await service._generate_efficiency_metrics()

        # Check for efficiency alert
        found_efficiency_alert = False
        for call in alert_callback.call_args_list:
            alert = call[0][0]
            if alert.insight_type == InsightType.EFFICIENCY_DROP:
                found_efficiency_alert = True
                assert alert.severity == AlertSeverity.WARNING
                break

        assert found_efficiency_alert


class TestAlertManagement:
    """Test alert creation and management."""

    @pytest.mark.asyncio
    async def test_create_alert(self, analytics_service):
        """Test alert creation."""
        alert = await analytics_service._create_alert(
            severity=AlertSeverity.WARNING,
            insight_type=InsightType.ANOMALY,
            message="Test alert",
            data={"test": "data"},
        )

        assert alert.id.startswith("ALT-")
        assert alert.severity == AlertSeverity.WARNING
        assert alert.acknowledged is False

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, analytics_service):
        """Test alert acknowledgment."""
        # Create an alert
        alert = await analytics_service._create_alert(
            severity=AlertSeverity.INFO,
            insight_type=InsightType.PATTERN,
            message="Acknowledgement test",
            data={},
        )

        # Acknowledge it
        result = await analytics_service.acknowledge_alert(alert.id, "test_user")

        assert result is True

        # Verify it's acknowledged
        alerts = analytics_service.get_alerts(acknowledged=True)
        assert any(a.id == alert.id for a in alerts)

    @pytest.mark.asyncio
    async def test_get_alerts_filtered(self, analytics_service):
        """Test filtering alerts by severity."""
        # Create alerts of different severities
        await analytics_service._create_alert(AlertSeverity.INFO, InsightType.PATTERN, "Info", {})
        await analytics_service._create_alert(AlertSeverity.WARNING, InsightType.IMBALANCE, "Warning", {})
        await analytics_service._create_alert(AlertSeverity.CRITICAL, InsightType.SPIKE_DETECTED, "Critical", {})

        # Filter by severity
        critical_alerts = analytics_service.get_alerts(severity=AlertSeverity.CRITICAL)

        assert len(critical_alerts) == 1
        assert critical_alerts[0].severity == AlertSeverity.CRITICAL


class TestCoreQueries:
    """Test the three core investigative queries."""

    @pytest.mark.asyncio
    async def test_impact_distribution_query(self, analytics_service):
        """Test Query 1: Impact Distribution."""
        # Add events with different types and impacts
        await analytics_service.ingest_event({"type": "TYPE_A", "impact": 0.8})
        await analytics_service.ingest_event({"type": "TYPE_A", "impact": 0.6})
        await analytics_service.ingest_event({"type": "TYPE_B", "impact": 0.4})

        result = await analytics_service.execute_impact_distribution_query()

        assert result["query"] == "impact_distribution"
        assert "TYPE_A" in result["distribution"]
        assert "TYPE_B" in result["distribution"]
        assert result["distribution"]["TYPE_A"]["mean_impact"] == 0.7  # (0.8 + 0.6) / 2
        assert result["distribution"]["TYPE_A"]["count"] == 2

    @pytest.mark.asyncio
    async def test_hot_activities_query(self, analytics_service):
        """Test Query 2: Hot Activities."""
        # Add events for different activities
        for i in range(15):
            await analytics_service.ingest_event(
                {
                    "type": "EVENT",
                    "impact": 0.5,
                    "data": {"activity_id": "hot_activity"},
                }
            )

        for i in range(5):
            await analytics_service.ingest_event(
                {
                    "type": "EVENT",
                    "impact": 0.5,
                    "data": {"activity_id": "cold_activity"},
                }
            )

        result = await analytics_service.execute_hot_activities_query(density_threshold=10)

        assert result["query"] == "hot_activities"
        assert "hot_activity" in result["hot_activities"]
        assert "cold_activity" not in result["hot_activities"]

    @pytest.mark.asyncio
    async def test_temporal_flow_query(self, analytics_service):
        """Test Query 3: Temporal Flow with Rolling Impact."""
        # Add time-ordered events
        base_time = datetime.now(UTC)
        for i in range(10):
            await analytics_service.ingest_event(
                {
                    "type": "FLOW_EVENT",
                    "impact": 0.1 * (i + 1),  # Increasing impact
                    "timestamp": (base_time + timedelta(seconds=i)).isoformat(),
                }
            )

        result = await analytics_service.execute_temporal_flow_query(window_size=3)

        assert result["query"] == "temporal_flow"
        assert len(result["flow"]) == 10

        # Check rolling impact is calculated
        for entry in result["flow"]:
            assert "rolling_impact" in entry


class TestServiceLifecycle:
    """Test service start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_stop(self, analytics_service):
        """Test starting and stopping the service."""
        await analytics_service.start()

        assert analytics_service._is_running is True

        await analytics_service.stop()

        assert analytics_service._is_running is False

    @pytest.mark.asyncio
    async def test_double_start_warning(self, analytics_service, caplog):
        """Test that double-starting logs a warning."""
        await analytics_service.start()
        await analytics_service.start()  # Should warn

        assert "already running" in caplog.text.lower()

        await analytics_service.stop()


class TestSpikeAndBalanceSummaries:
    """Test spike summary and balance report retrieval."""

    @pytest.mark.asyncio
    async def test_get_latest_spike_summary(self, analytics_service):
        """Test retrieving latest spike summary."""
        # Initially empty
        assert analytics_service.get_latest_spike_summary() is None

        # Generate a summary
        await analytics_service._generate_spike_summary()

        summary = analytics_service.get_latest_spike_summary()
        assert isinstance(summary, SpikeSummary)

    @pytest.mark.asyncio
    async def test_get_latest_balance_report(self, analytics_service):
        """Test retrieving latest balance report."""
        # Initially empty
        assert analytics_service.get_latest_balance_report() is None

        # Generate a report
        await analytics_service._generate_balance_report()

        report = analytics_service.get_latest_balance_report()
        assert isinstance(report, BalanceReport)


class TestStatistics:
    """Test statistics retrieval."""

    @pytest.mark.asyncio
    async def test_get_statistics(self, analytics_service):
        """Test comprehensive statistics."""
        # Add some data
        await analytics_service.ingest_event({"type": "A", "impact": 0.95})
        await analytics_service.ingest_event({"type": "B", "impact": 0.3})

        await analytics_service._create_alert(AlertSeverity.INFO, InsightType.PATTERN, "Test", {})

        stats = analytics_service.get_statistics()

        assert stats["total_events_processed"] == 2
        assert stats["high_impact_events"] == 1
        assert stats["total_alerts"] == 1
        assert "event_type_counts" in stats
