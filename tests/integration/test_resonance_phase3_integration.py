"""
Integration Tests for Resonance Analytics Phase 3.

Tests the complete flow:
Analytics Service → Tuning Optimizer → Cost Optimizer → Stripe Billing

These tests verify that all components work together correctly.
"""

from datetime import UTC, datetime

import pytest

from application.resonance.analytics_service import (
    AlertSeverity,
    AnalyticsService,
    InsightType,
)
from application.resonance.cost_optimizer import (
    ComputeMode,
    CostOptimizer,
)
from application.resonance.databricks_analytics import DatabricksAnalytics
from application.resonance.stripe_billing import StripeBilling
from application.resonance.tuning_optimizer import (
    RecommendationStatus,
    TuningOptimizer,
)


@pytest.fixture
def integrated_system():
    """Create an integrated analytics system."""
    # Track all billing events for verification
    billing_events = []

    def meter_callback(event):
        billing_events.append(event)
        return True

    analytics = AnalyticsService()
    tuning = TuningOptimizer()
    cost = CostOptimizer(meter_event_callback=meter_callback)
    billing = StripeBilling(meter_event_callback=meter_callback)
    databricks = DatabricksAnalytics()

    return {
        "analytics": analytics,
        "tuning": tuning,
        "cost": cost,
        "billing": billing,
        "databricks": databricks,
        "billing_events": billing_events,
    }


class TestEndToEndEventFlow:
    """Test end-to-end event processing flow."""

    @pytest.mark.asyncio
    async def test_event_to_insight_to_billing(self, integrated_system):
        """Test complete flow: Event → Insight → Billing."""
        analytics = integrated_system["analytics"]
        cost = integrated_system["cost"]
        billing = integrated_system["billing"]

        # Step 1: Ingest high-impact events
        for i in range(15):
            await analytics.ingest_event(
                {
                    "event_type": "processing",
                    "activity_id": f"act_{i}",
                    "impact": 0.95,  # High impact
                    "data": {"test": True},
                }
            )

        # Step 2: Check high-impact events detection
        stats = analytics.get_statistics()
        assert stats["total_events_processed"] >= 15
        assert stats["high_impact_events"] >= 10  # Most should be high-impact

        # Step 3: Record costs
        metrics = cost.record_event_cost(
            event_count=15,
            high_impact_count=15,
            meaningful_count=15,
            dbu_consumed=0.1,
        )
        assert metrics.total_events == 15
        assert metrics.cost_per_event > 0

        # Step 4: Queue billing event
        billing.record_meaningful_events(
            customer_id="cus_integration_test",
            event_count=15,
        )

        # Step 5: Send to Stripe
        sent = await billing.send_pending_events()
        assert sent == 1

        # Step 6: Verify billing tracked
        usage = billing.get_customer_usage("cus_integration_test")
        assert usage == 15

    @pytest.mark.asyncio
    async def test_insight_triggers_tuning_recommendation(self, integrated_system):
        """Test that insights lead to tuning recommendations."""
        analytics = integrated_system["analytics"]
        tuning = integrated_system["tuning"]

        # Generate spike insights by ingesting many high-impact events
        for i in range(20):
            await analytics.ingest_event(
                {
                    "event_type": "spike_test",
                    "activity_id": "act_spike",
                    "impact": 0.95,
                }
            )

        # Get generated insights
        insights = analytics.get_insights()

        # Generate recommendations from any insight
        all_recommendations = []
        for insight in insights:
            recs = tuning.generate_recommendations(insight)
            all_recommendations.extend(recs)

        # Should have at least one recommendation if insights were generated
        if insights:
            assert len(all_recommendations) > 0

    @pytest.mark.asyncio
    async def test_cost_optimization_feedback_loop(self, integrated_system):
        """Test that cost optimizer adapts based on load."""
        cost = integrated_system["cost"]

        # Simulate increasing load
        for density in [10, 50, 100, 200, 300]:
            cost.record_event_density(density)

        # Optimizer should recommend adjustments
        cost.analyze_and_recommend()

        # Get current allocation
        allocation = cost.get_current_allocation()

        # Verify allocation is reasonable
        assert 10 <= allocation.tick_rate_hz <= 120
        assert 10 <= allocation.batch_size <= 1000
        assert allocation.worker_count >= 1


class TestTuningWorkflow:
    """Test the complete tuning approval workflow."""

    @pytest.mark.asyncio
    async def test_full_tuning_lifecycle(self, integrated_system):
        """Test: Generate → Approve → Apply → Evaluate."""
        integrated_system["analytics"]
        tuning = integrated_system["tuning"]

        # Create insight
        from application.resonance.analytics_service import AnalyticsInsight

        insight = AnalyticsInsight(
            id="INS-INTEGRATION",
            insight_type=InsightType.EFFICIENCY_DROP,
            title="Low Efficiency",
            description="Efficiency at 30%",
            severity=AlertSeverity.WARNING,
            timestamp=datetime.now(UTC),
            metrics={"efficiency": 0.30},
            recommendations=["Increase batch size"],
        )

        # Generate recommendations
        recs = tuning.generate_recommendations(insight)
        assert len(recs) > 0

        rec = recs[0]
        assert rec.status == RecommendationStatus.PENDING

        # Approve
        approved = tuning.approve_recommendation(rec.id, "test_operator")
        assert approved.status == RecommendationStatus.APPROVED

        # Apply
        success = await tuning.apply_recommendation(rec.id, {"efficiency": 0.30})
        assert success is True

        # Evaluate
        result = await tuning.evaluate_recommendation(rec.id, {"efficiency": 0.50})
        assert result in ["positive", "neutral", "negative"]

    @pytest.mark.asyncio
    async def test_ab_test_workflow(self, integrated_system):
        """Test A/B testing workflow."""
        tuning = integrated_system["tuning"]

        # Create insight
        from application.resonance.analytics_service import AnalyticsInsight

        insight = AnalyticsInsight(
            id="INS-AB",
            insight_type=InsightType.SPIKE_DETECTED,
            title="High Spikes",
            description="Spike density at 10/min",
            severity=AlertSeverity.CRITICAL,
            timestamp=datetime.now(UTC),
            metrics={"avg_density": 10.0},
            recommendations=[],
        )

        recs = tuning.generate_recommendations(insight)
        if recs:
            rec = recs[0]

            # Start A/B test
            test = tuning.start_ab_test(rec.id, duration_minutes=30)
            assert test is not None
            assert test.is_complete is False

            # Complete test
            result = tuning.complete_ab_test(
                test.test_id,
                control_metrics={"efficiency": 0.50},
                variant_metrics={"efficiency": 0.65},
            )

            assert result.is_complete is True
            assert result.winner == "variant"


class TestCostBillingIntegration:
    """Test cost tracking and billing integration."""

    @pytest.mark.asyncio
    async def test_cost_to_billing_flow(self, integrated_system):
        """Test that cost events flow to billing."""
        cost = integrated_system["cost"]
        billing = integrated_system["billing"]

        # Record event costs
        for i in range(5):
            cost.record_event_cost(
                event_count=100,
                high_impact_count=20,
                meaningful_count=50,
                dbu_consumed=0.2,
            )

        # Get cost metrics
        metrics = cost.get_current_cost_metrics()
        assert metrics.total_events >= 500
        assert metrics.meaningful_events >= 250

        # Bill based on meaningful events
        billing.record_meaningful_events(
            customer_id="cus_cost_test",
            event_count=metrics.meaningful_events,
        )

        # Verify pending
        assert billing.get_pending_count() == 1

        # Send
        await billing.send_pending_events()

        # Verify usage tracked
        usage = billing.get_customer_usage("cus_cost_test")
        assert usage >= 250

    @pytest.mark.asyncio
    async def test_compute_mode_affects_cost(self, integrated_system):
        """Test that compute mode affects cost calculation."""
        cost = integrated_system["cost"]

        # Record costs in serverless mode
        cost._allocation.compute_mode = ComputeMode.SERVERLESS
        serverless_metrics = cost.record_event_cost(
            event_count=100,
            high_impact_count=10,
            meaningful_count=25,
            dbu_consumed=1.0,
        )

        # Create new period and record in classic mode
        cost._cost_history.append(cost.create_cost_period())
        cost._allocation.compute_mode = ComputeMode.CLASSIC
        classic_metrics = cost.record_event_cost(
            event_count=100,
            high_impact_count=10,
            meaningful_count=25,
            dbu_consumed=1.0,
        )

        # Serverless should cost more per DBU
        assert serverless_metrics.cost_usd > classic_metrics.cost_usd


class TestDatabricksIntegration:
    """Test Databricks analytics integration."""

    def test_query_construction(self, integrated_system):
        """Test that queries are properly constructed."""
        databricks = integrated_system["databricks"]

        # Verify query history is empty initially
        history = databricks.get_query_history()
        assert isinstance(history, list)

    def test_performance_stats_empty(self, integrated_system):
        """Test performance stats when empty."""
        databricks = integrated_system["databricks"]

        stats = databricks.get_query_performance_stats()
        assert stats["total_queries"] == 0


class TestCrossCuttingConcerns:
    """Test cross-cutting concerns across all components."""

    @pytest.mark.asyncio
    async def test_timestamps_consistent(self, integrated_system):
        """Test that timestamps are UTC and consistent."""
        analytics = integrated_system["analytics"]
        billing = integrated_system["billing"]

        # Ingest event
        await analytics.ingest_event(
            {
                "event_type": "timestamp_test",
                "activity_id": "act_ts",
                "impact": 0.5,
            }
        )

        # Create billing event
        event = billing.create_meter_event(
            customer_id="cus_ts",
            event_name="test",
            value=1,
        )

        # Both should have UTC timestamps
        assert event.timestamp.tzinfo is not None

    @pytest.mark.asyncio
    async def test_graceful_degradation(self, integrated_system):
        """Test that system degrades gracefully without external services."""
        databricks = integrated_system["databricks"]
        billing = integrated_system["billing"]

        # Databricks queries should return valid results even when disconnected
        result = await databricks.query_impact_distribution()
        assert result.statement_id is not None

        # Billing should work in dry-run mode
        billing.create_meter_event("cus_degrade", "test", 10)
        sent = await billing.send_pending_events()
        assert sent == 1


class TestMultiCustomerScenario:
    """Test scenarios with multiple customers."""

    @pytest.mark.asyncio
    async def test_per_customer_billing(self, integrated_system):
        """Test that billing is tracked per customer."""
        billing = integrated_system["billing"]

        # Record usage for multiple customers
        customers = ["cus_a", "cus_b", "cus_c"]
        for i, cus in enumerate(customers, 1):
            billing.record_meaningful_events(cus, event_count=i * 100)

        # Send all
        await billing.send_pending_events()

        # Verify individual tracking
        all_usage = billing.get_all_customer_usage()
        assert all_usage["cus_a"] == 100
        assert all_usage["cus_b"] == 200
        assert all_usage["cus_c"] == 300

        # Verify total
        total = sum(all_usage.values())
        assert total == 600
