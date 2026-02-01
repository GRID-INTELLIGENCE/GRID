#!/usr/bin/env python
"""
Resonance Analytics Demo - Phase 3 Cost Optimization.

This demo shows the complete analytics and billing flow:
1. Event ingestion and spike detection
2. Insight generation and tuning recommendations
3. Cost tracking and optimization
4. Usage-based billing with Stripe

Run this demo:
    python examples/resonance_analytics_demo.py
"""

import asyncio
import logging
from datetime import UTC, datetime
from random import choice, random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("demo")


async def demo_analytics_service():
    """Demo 1: Analytics Service with Spike Detection."""
    print("\n" + "=" * 60)
    print("DEMO 1: Analytics Service - Spike Detection")
    print("=" * 60)

    from application.resonance.analytics_service import AnalyticsService

    # Create service
    analytics = AnalyticsService()

    # Simulate event stream with varying impact
    event_types = ["query", "processing", "enrich", "transform", "output"]

    print("\n📊 Ingesting 50 events with varying impact levels...")
    for i in range(50):
        # Mix of low and high impact events
        if i % 5 == 0:
            impact = 0.92 + random() * 0.08  # High impact (spikes)
        else:
            impact = 0.2 + random() * 0.5  # Normal impact

        await analytics.ingest_event(
            {
                "event_type": choice(event_types),
                "activity_id": f"demo_activity_{i % 10}",
                "impact": impact,
                "data": {"demo": True, "batch": i // 10},
            }
        )

        if (i + 1) % 10 == 0:
            print(f"  ✓ Ingested {i + 1} events")

    # Get statistics
    stats = analytics.get_statistics()
    print("\n📈 Statistics:")
    print(f"  • Total events: {stats['total_events_processed']}")
    print(f"  • High-impact events: {stats['spike_events_detected']}")
    print(f"  • Alerts generated: {stats['alerts_generated']}")
    print(f"  • Insights generated: {stats['insights_generated']}")

    # Show any alerts
    alerts = analytics.get_alerts(acknowledged=False)
    if alerts:
        print("\n🚨 Active Alerts:")
        for alert in alerts[:3]:
            print(f"  • [{alert.severity.value.upper()}] {alert.title}")

    # Show insights
    insights = analytics.get_insights()
    if insights:
        print("\n💡 Generated Insights:")
        for insight in insights[:3]:
            print(f"  • [{insight.insight_type.value}] {insight.title}")

    return analytics, insights


async def demo_tuning_optimizer(insights):
    """Demo 2: Tuning Optimizer with HITL Workflow."""
    print("\n" + "=" * 60)
    print("DEMO 2: Tuning Optimizer - Recommendation Workflow")
    print("=" * 60)

    from application.resonance.analytics_service import (
        AlertSeverity,
        AnalyticsInsight,
        InsightType,
    )
    from application.resonance.tuning_optimizer import TuningOptimizer

    optimizer = TuningOptimizer()

    # Use insights from analytics or create a demo insight
    if insights:
        insight = insights[0]
    else:
        insight = AnalyticsInsight(
            id="INS-DEMO001",
            insight_type=InsightType.EFFICIENCY_DROP,
            title="System Efficiency Below Target",
            description="Processing efficiency has dropped to 35%",
            severity=AlertSeverity.WARNING,
            timestamp=datetime.now(UTC),
            metrics={"efficiency": 0.35, "target": 0.70},
            recommendations=["Consider increasing batch size"],
        )

    print(f"\n🎯 Processing insight: {insight.title}")

    # Generate recommendations
    recommendations = optimizer.generate_recommendations(insight)
    print(f"\n📋 Generated {len(recommendations)} recommendations:")

    for rec in recommendations:
        print(f"\n  Recommendation: {rec.id}")
        print(f"  • Parameter: {rec.parameter.value}")
        print(f"  • Current value: {rec.current_value}")
        print(f"  • Recommended: {rec.recommended_value}")
        print(f"  • Confidence: {rec.confidence:.1%}")
        print(f"  • Expected improvement: {rec.expected_improvement}")

    if recommendations:
        rec = recommendations[0]

        # Simulate HITL approval
        print(f"\n👨‍💻 Operator 'demo_user' approving recommendation {rec.id}...")
        optimizer.approve_recommendation(rec.id, "demo_user")
        print("  ✓ Approved!")

        # Apply the change
        print("\n⚙️ Applying recommendation...")
        success = await optimizer.apply_recommendation(rec.id, {"efficiency": 0.35})  # Before metrics
        print(f"  ✓ Applied: {success}")

        # Simulate evaluation after some time
        print("\n📊 Evaluating after applying change...")
        result = await optimizer.evaluate_recommendation(rec.id, {"efficiency": 0.55})  # After metrics (improved)
        print(f"  ✓ Result: {result}")

    return optimizer


async def demo_cost_optimizer():
    """Demo 3: Cost Optimizer with Adaptive Tuning."""
    print("\n" + "=" * 60)
    print("DEMO 3: Cost Optimizer - Adaptive Resource Management")
    print("=" * 60)

    from application.resonance.cost_optimizer import CostOptimizer, CostTier

    # Custom meter callback for demo
    billed_events = []

    def demo_meter_callback(event):
        billed_events.append(event)
        print(f"  📤 Stripe event: {event.event_name} = {event.value}")
        return True

    optimizer = CostOptimizer(
        cost_tier=CostTier.STANDARD,
        meter_event_callback=demo_meter_callback,
    )

    # Get initial allocation
    allocation = optimizer.get_current_allocation()
    print("\n🎚️ Initial Resource Allocation:")
    print(f"  • Tick rate: {allocation.tick_rate_hz} Hz")
    print(f"  • Batch size: {allocation.batch_size}")
    print(f"  • Worker count: {allocation.worker_count}")
    print(f"  • Compute mode: {allocation.compute_mode.value}")

    # Simulate varying load
    print("\n📈 Simulating varying load patterns...")
    load_patterns = [
        ("Low traffic", [5, 8, 3, 6, 4]),
        ("Normal traffic", [40, 55, 60, 45, 50]),
        ("High traffic", [150, 180, 200, 175, 190]),
        ("Traffic spike", [400, 550, 600, 500, 450]),
    ]

    for pattern_name, densities in load_patterns:
        print(f"\n  📊 {pattern_name}:")
        for density in densities:
            optimizer.record_event_density(density)

        optimal_tick = optimizer.calculate_optimal_tick_rate()
        optimal_batch = optimizer.calculate_optimal_batch_size()
        optimal_mode = optimizer.calculate_optimal_compute_mode()

        print(f"     Optimal tick rate: {optimal_tick} Hz")
        print(f"     Optimal batch size: {optimal_batch}")
        print(f"     Optimal compute mode: {optimal_mode.value}")

    # Record costs
    print("\n💰 Recording event costs...")
    for i in range(3):
        metrics = optimizer.record_event_cost(
            event_count=1000,
            high_impact_count=100,
            meaningful_count=250,
            dbu_consumed=0.5,
        )

    current_metrics = optimizer.get_current_cost_metrics()
    print("\n📊 Cost Metrics:")
    print(f"  • Total events: {current_metrics.total_events}")
    print(f"  • Meaningful events: {current_metrics.meaningful_events}")
    print(f"  • DBU consumed: {current_metrics.dbu_consumed:.2f}")
    print(f"  • Total cost: ${current_metrics.cost_usd:.4f}")
    print(f"  • Cost per event: ${current_metrics.cost_per_event:.6f}")
    print(f"  • Cost per meaningful event: ${current_metrics.cost_per_meaningful_event:.6f}")

    # Queue billing events
    print("\n📊 Queueing billing event...")
    optimizer.queue_meter_event(
        customer_id="cus_demo123",
        event_name="resonance_meaningful_events",
        value=current_metrics.meaningful_events,
    )

    # Flush to Stripe
    print("\n📤 Flushing to Stripe billing...")
    sent = await optimizer.flush_meter_events()
    print(f"  ✓ Sent {sent} meter event(s)")

    # Get optimization recommendations
    print("\n💡 Optimization Recommendations:")
    recommendations = optimizer.analyze_and_recommend()
    for rec in recommendations:
        savings_str = (
            f"+{rec.expected_savings_pct:.0f}% cost savings"
            if rec.expected_savings_pct > 0
            else f"{rec.expected_savings_pct:.0f}% cost increase (but faster)"
        )
        print(f"  • [{rec.category}] {rec.current_value} → {rec.recommended_value}")
        print(f"    Rationale: {rec.rationale}")
        print(f"    Expected: {savings_str}")

    return optimizer


async def demo_stripe_billing():
    """Demo 4: Stripe Billing Integration."""
    print("\n" + "=" * 60)
    print("DEMO 4: Stripe Billing - Usage-Based Pricing")
    print("=" * 60)

    from application.resonance.stripe_billing import StripeBilling

    # Create billing with demo callback
    def demo_stripe_callback(event):
        print("  → API: POST /v1/billing/meter_events")
        print(f"         event_name: {event.event_name}")
        print(f"         customer: {event.customer_id}")
        print(f"         value: {event.value}")
        return True

    billing = StripeBilling(meter_event_callback=demo_stripe_callback)

    print("\n💳 Recording usage for multiple customers...")

    # Simulate multiple customers with different usage
    customers = [
        ("cus_startup", 500, "Startup Co"),
        ("cus_enterprise", 5000, "Enterprise Inc"),
        ("cus_scale", 50000, "ScaleUp Ltd"),
    ]

    for cus_id, events, name in customers:
        print(f"\n  📊 {name} ({cus_id}):")

        # Record meaningful events
        billing.record_meaningful_events(cus_id, events)
        print(f"     Meaningful events: {events}")

        # Also record high-impact events (subset)
        high_impact = int(events * 0.1)  # 10%
        billing.record_high_impact_events(cus_id, high_impact)
        print(f"     High-impact events: {high_impact}")

    print("\n📤 Sending meter events to Stripe...")
    sent = await billing.send_pending_events()
    print(f"  ✓ Sent {sent} events")

    print("\n📊 Usage Summary:")
    all_usage = billing.get_all_customer_usage()
    for cus_id, usage in all_usage.items():
        name = next(n for c, _, n in customers if c == cus_id)
        print(f"  • {name}: {usage:,} billable events")

    print("\n💵 Invoice Previews:")
    for cus_id, _, name in customers:
        preview = await billing.get_upcoming_invoice(cus_id)
        print(f"  • {name}: ${preview.amount_due:.2f} {preview.currency.upper()}")

    # Get billing stats
    stats = billing.get_billing_stats()
    print("\n📈 Billing Stats:")
    print(f"  • Events sent: {stats['events_sent']}")
    print(f"  • Customers tracked: {stats['customers_tracked']}")
    print(f"  • Total usage: {stats['total_usage']:,}")

    return billing


async def demo_databricks_queries():
    """Demo 5: Databricks Analytics Queries."""
    print("\n" + "=" * 60)
    print("DEMO 5: Databricks Analytics - SQL Queries")
    print("=" * 60)

    from application.resonance.databricks_analytics import DatabricksAnalytics

    analytics = DatabricksAnalytics()

    print("\n📊 Available Analytics Queries:")
    print(
        """
    These queries run against Databricks SQL Warehouse when connected:

    1. Impact Distribution
       - Aggregates events by type with mean/max/min impact
       - Identifies which event types generate highest impact

    2. Hot Activities
       - Finds activities exceeding event density threshold
       - Useful for identifying bottlenecks

    3. Temporal Flow
       - Calculates rolling average impact over time
       - Detects sustained anomalies

    4. Cost Efficiency
       - Joins event stats with DBU billing data
       - Calculates cost per meaningful event
    """
    )

    print("\n⚡ Running queries (dry-run mode)...")

    # Execute queries (will return mock results in dry-run)
    queries = [
        ("Impact Distribution", analytics.query_impact_distribution()),
        ("Hot Activities", analytics.query_hot_activities(threshold=50)),
        ("Temporal Flow", analytics.query_temporal_flow(window_minutes=5)),
        ("Cost Efficiency", analytics.query_cost_efficiency()),
    ]

    for name, query_coro in queries:
        result = await query_coro
        print(f"  ✓ {name}: {result.status}")

    # Show performance stats
    stats = analytics.get_query_performance_stats()
    print("\n📊 Query Performance Stats:")
    print(f"  • Total queries: {stats['total_queries']}")
    print(f"  • Avg duration: {stats['avg_duration_ms']:.1f}ms")
    print(f"  • Est. DBU consumed: {stats['estimated_dbu']:.4f}")

    return analytics


async def main():
    """Run all demos."""
    print("\n" + "🚀 " * 20)
    print("RESONANCE ANALYTICS OPTIMIZATION - PHASE 3 DEMO")
    print("🚀 " * 20)

    # Demo 1: Analytics
    analytics, insights = await demo_analytics_service()

    # Demo 2: Tuning
    tuning = await demo_tuning_optimizer(insights)

    # Demo 3: Cost Optimization
    cost = await demo_cost_optimizer()

    # Demo 4: Stripe Billing
    billing = await demo_stripe_billing()

    # Demo 5: Databricks
    databricks = await demo_databricks_queries()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)
    print(
        """
    Summary of Phase 3 Implementation:

    ✅ Analytics Service
       - Real-time spike detection
       - Modality balance monitoring
       - Efficiency metrics

    ✅ Tuning Optimizer
       - Insight-to-parameter mapping
       - HITL approval workflow
       - A/B testing framework

    ✅ Cost Optimizer
       - Adaptive tick-rate (10-120 Hz)
       - Smart batching (10-1000)
       - Compute mode switching

    ✅ Stripe Billing
       - Usage-based pricing
       - Meter events API
       - Per-customer tracking

    ✅ Databricks Analytics
       - SQL statement execution
       - Billing usage queries
       - Query performance tracking

    See the documentation for production deployment instructions.
    """
    )


if __name__ == "__main__":
    asyncio.run(main())
