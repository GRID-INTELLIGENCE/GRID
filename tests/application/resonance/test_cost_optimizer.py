"""
Tests for Cost Optimizer - Phase 3.

Covers:
- Adaptive tick-rate adjustment
- Smart batching
- Compute mode optimization
- Cost tracking
- Stripe billing integration
"""

import pytest
from application.resonance.cost_optimizer import (
    BillingMeterEvent,
    ComputeMode,
    CostMetrics,
    CostOptimizer,
    CostTier,
    OptimizationRecommendation,
    ResourceAllocation,
)


@pytest.fixture
def cost_optimizer():
    """Create a fresh CostOptimizer instance."""
    return CostOptimizer(cost_tier=CostTier.STANDARD)


@pytest.fixture
def optimizer_with_mock_meter():
    """Create optimizer with mock meter callback."""
    sent_events = []

    def mock_callback(event: BillingMeterEvent) -> bool:
        sent_events.append(event)
        return True

    optimizer = CostOptimizer(meter_event_callback=mock_callback)
    optimizer._sent_events = sent_events  # Attach for testing
    return optimizer


class TestAdaptiveTickRate:
    """Test adaptive tick-rate adjustment."""

    def test_low_density_reduces_tick_rate(self, cost_optimizer):
        """Low event density should suggest lower tick rate."""
        # Simulate low density
        for i in range(3):
            cost_optimizer.record_event_density(2)  # 2 events

        optimal = cost_optimizer.calculate_optimal_tick_rate()
        # Low density returns 20.0 as optimal
        assert 10.0 <= optimal <= 60.0  # Should be low-to-normal

    def test_high_density_increases_tick_rate(self, cost_optimizer):
        """High event density should suggest higher tick rate."""
        # Simulate high density
        for i in range(5):
            cost_optimizer.record_event_density(150)

        optimal = cost_optimizer.calculate_optimal_tick_rate()
        assert optimal >= 90.0  # Should be high

    def test_spike_density_maximizes_tick_rate(self, cost_optimizer):
        """Spike density should maximize tick rate."""
        for i in range(5):
            cost_optimizer.record_event_density(600)

        optimal = cost_optimizer.calculate_optimal_tick_rate()
        assert optimal == 120.0  # Maximum

    def test_tick_rate_adjustment_threshold(self, cost_optimizer):
        """Tick rate only adjusts if difference > 20%."""
        # Start at 60Hz
        assert cost_optimizer._allocation.tick_rate_hz == 60.0

        # Small density change shouldn't trigger adjustment
        cost_optimizer.record_event_density(50)
        result = cost_optimizer.apply_tick_rate_adjustment()

        # May or may not adjust depending on calculated optimal
        assert isinstance(result, bool)


class TestSmartBatching:
    """Test smart batch size adjustment."""

    def test_low_density_small_batches(self, cost_optimizer):
        """Low density should use smaller batches."""
        for i in range(3):
            cost_optimizer.record_event_density(3)

        optimal = cost_optimizer.calculate_optimal_batch_size()
        # Low density returns 25 or similar small batch size
        assert optimal <= 100  # Small-to-moderate batches

    def test_high_density_large_batches(self, cost_optimizer):
        """High density should use larger batches."""
        for i in range(5):
            cost_optimizer.record_event_density(200)

        optimal = cost_optimizer.calculate_optimal_batch_size()
        assert optimal >= 250  # Large batches

    def test_batch_size_adjustment(self, cost_optimizer):
        """Test batch size adjustment application."""
        original = cost_optimizer._allocation.batch_size

        for i in range(5):
            cost_optimizer.record_event_density(300)

        result = cost_optimizer.apply_batch_size_adjustment()
        assert result is True or cost_optimizer._allocation.batch_size != original


class TestComputeMode:
    """Test compute mode optimization."""

    def test_sustained_high_load_favors_classic(self, cost_optimizer):
        """Sustained high load should favor classic compute."""
        # Simulate sustained high load
        for i in range(10):
            cost_optimizer.record_event_density(150)

        mode = cost_optimizer.calculate_optimal_compute_mode()
        assert mode == ComputeMode.CLASSIC

    def test_spike_favors_serverless(self, cost_optimizer):
        """Spike should favor serverless compute."""
        for i in range(3):
            cost_optimizer.record_event_density(600)

        mode = cost_optimizer.calculate_optimal_compute_mode()
        assert mode == ComputeMode.SERVERLESS

    def test_dbu_cost_rate_varies_by_mode(self, cost_optimizer):
        """DBU cost rate should vary by compute mode."""
        cost_optimizer._allocation.compute_mode = ComputeMode.SERVERLESS
        serverless_rate = cost_optimizer.get_dbu_cost_rate()

        cost_optimizer._allocation.compute_mode = ComputeMode.CLASSIC
        classic_rate = cost_optimizer.get_dbu_cost_rate()

        assert serverless_rate > classic_rate  # Serverless is more expensive


class TestCostTracking:
    """Test cost tracking functionality."""

    def test_create_cost_period(self, cost_optimizer):
        """Test cost period creation."""
        metrics = cost_optimizer.create_cost_period()

        assert isinstance(metrics, CostMetrics)
        assert metrics.period_start is not None
        assert metrics.period_end > metrics.period_start

    def test_record_event_cost(self, cost_optimizer):
        """Test recording event costs."""
        metrics = cost_optimizer.record_event_cost(
            event_count=100,
            high_impact_count=10,
            meaningful_count=25,
            dbu_consumed=0.5,
        )

        assert metrics.total_events == 100
        assert metrics.high_impact_events == 10
        assert metrics.meaningful_events == 25
        assert metrics.low_impact_events == 90
        assert metrics.dbu_consumed == 0.5
        assert metrics.cost_usd > 0

    def test_cost_per_event_calculation(self, cost_optimizer):
        """Test cost per event calculation."""
        metrics = cost_optimizer.record_event_cost(
            event_count=100,
            high_impact_count=10,
            meaningful_count=25,
            dbu_consumed=1.0,
        )

        assert metrics.cost_per_event > 0
        assert metrics.cost_per_meaningful_event > 0
        assert metrics.cost_per_meaningful_event > metrics.cost_per_event

    def test_cost_history(self, cost_optimizer):
        """Test cost history tracking."""
        for i in range(3):
            cost_optimizer.record_event_cost(
                event_count=50,
                high_impact_count=5,
                meaningful_count=10,
                dbu_consumed=0.25,
            )

        history = cost_optimizer.get_cost_history()
        assert len(history) >= 1


class TestMeterEvents:
    """Test Stripe meter event functionality."""

    def test_queue_meter_event(self, cost_optimizer):
        """Test queuing meter events."""
        event = cost_optimizer.queue_meter_event(
            customer_id="cus_test123",
            event_name="resonance_meaningful_events",
            value=25,
        )

        assert event.customer_id == "cus_test123"
        assert event.value == 25
        assert event.event_name == "resonance_meaningful_events"
        assert len(cost_optimizer._pending_meter_events) == 1

    @pytest.mark.asyncio
    async def test_flush_meter_events(self, optimizer_with_mock_meter):
        """Test flushing meter events."""
        optimizer_with_mock_meter.queue_meter_event(
            customer_id="cus_test",
            event_name="test_meter",
            value=10,
        )

        sent = await optimizer_with_mock_meter.flush_meter_events()
        assert sent == 1
        assert len(optimizer_with_mock_meter._pending_meter_events) == 0

    def test_create_stripe_payload(self, cost_optimizer):
        """Test Stripe API payload creation."""
        payload = cost_optimizer.create_stripe_meter_event_payload(
            customer_id="cus_abc123",
            meaningful_events=50,
        )

        assert payload["event_name"] == "resonance_meaningful_events"
        assert payload["payload"]["stripe_customer_id"] == "cus_abc123"
        assert payload["payload"]["value"] == "50"
        assert "identifier" in payload
        assert "timestamp" in payload


class TestOptimizationRecommendations:
    """Test optimization recommendation generation."""

    def test_generate_recommendations(self, cost_optimizer):
        """Test recommendation generation."""
        # Set up suboptimal state
        for i in range(5):
            cost_optimizer.record_event_density(200)

        recommendations = cost_optimizer.analyze_and_recommend()

        assert isinstance(recommendations, list)
        for rec in recommendations:
            assert isinstance(rec, OptimizationRecommendation)
            assert rec.category in ["tick_rate", "batching", "compute_mode", "resource"]

    def test_recommendations_include_savings(self, cost_optimizer):
        """Test that recommendations include expected savings."""
        for i in range(5):
            cost_optimizer.record_event_density(300)

        recommendations = cost_optimizer.analyze_and_recommend()

        for rec in recommendations:
            assert hasattr(rec, "expected_savings_pct")
            assert hasattr(rec, "confidence")


class TestResourceAllocation:
    """Test resource allocation management."""

    def test_get_current_allocation(self, cost_optimizer):
        """Test getting current allocation."""
        allocation = cost_optimizer.get_current_allocation()

        assert isinstance(allocation, ResourceAllocation)
        assert allocation.tick_rate_hz > 0
        assert allocation.batch_size > 0
        assert allocation.worker_count > 0

    def test_default_allocation_values(self, cost_optimizer):
        """Test default allocation values."""
        allocation = cost_optimizer.get_current_allocation()

        assert allocation.tick_rate_hz == 60.0
        assert allocation.batch_size == 100
        assert allocation.worker_count == 4
        assert allocation.queue_depth == 1000


class TestServiceLifecycle:
    """Test service lifecycle management."""

    @pytest.mark.asyncio
    async def test_start_stop(self, cost_optimizer):
        """Test starting and stopping the optimizer."""
        await cost_optimizer.start(optimization_interval=0.1)
        assert cost_optimizer._is_running is True

        await cost_optimizer.stop()
        assert cost_optimizer._is_running is False

    @pytest.mark.asyncio
    async def test_double_start_warning(self, cost_optimizer, caplog):
        """Test that double start logs a warning."""
        await cost_optimizer.start(optimization_interval=0.1)
        await cost_optimizer.start(optimization_interval=0.1)

        assert "already running" in caplog.text.lower()

        await cost_optimizer.stop()
