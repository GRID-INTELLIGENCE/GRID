"""
Cost Optimization Service - Phase 3 Implementation.

Provides:
- Adaptive tick-rate adjustment based on event density
- Smart batching for efficient processing
- Resource allocation optimization
- Cost-per-insight tracking
- Databricks DBU cost correlation
- Stripe usage-based billing integration
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class CostTier(StrEnum):
    """Cost tiers for usage-based billing."""

    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class ComputeMode(StrEnum):
    """Compute mode for Databricks operations."""

    SERVERLESS = "serverless"  # Fast start, higher cost per DBU
    CLASSIC = "classic"  # Slower start, lower cost per DBU
    HYBRID = "hybrid"  # Auto-switching based on load


@dataclass
class CostMetrics:
    """Cost tracking metrics."""

    period_start: datetime
    period_end: datetime
    total_events: int = 0
    high_impact_events: int = 0
    low_impact_events: int = 0
    meaningful_events: int = 0
    dbu_consumed: float = 0.0
    cost_usd: float = 0.0
    cost_per_event: float = 0.0
    cost_per_meaningful_event: float = 0.0
    stripe_meter_events_sent: int = 0

    def calculate_derived(self) -> None:
        """Calculate derived metrics."""
        if self.total_events > 0:
            self.cost_per_event = self.cost_usd / self.total_events
        if self.meaningful_events > 0:
            self.cost_per_meaningful_event = self.cost_usd / self.meaningful_events


@dataclass
class BillingMeterEvent:
    """Stripe billing meter event representation."""

    id: str
    event_name: str
    customer_id: str
    value: int
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    sent: bool = False
    sent_at: datetime | None = None


@dataclass
class ResourceAllocation:
    """Current resource allocation."""

    tick_rate_hz: float  # Events per second
    batch_size: int
    worker_count: int
    queue_depth: int
    compute_mode: ComputeMode
    dbu_limit_per_hour: float


@dataclass
class OptimizationRecommendation:
    """Recommendation for cost optimization."""

    id: str
    category: str  # "tick_rate", "batching", "compute_mode", "resource"
    current_value: Any
    recommended_value: Any
    expected_savings_pct: float
    rationale: str
    confidence: float


class CostOptimizer:
    """
    Cost & Performance Optimization Engine.

    Implements Phase 3 of the Resonance Analytics Optimization:
    - Adaptive tick-rate adjustment (10-120 Hz)
    - Smart batching (10-1000 events)
    - Compute mode switching (Serverless/Classic/Hybrid)
    - Cost-per-insight tracking
    - Stripe billing integration
    """

    # Thresholds for adaptive adjustment
    LOW_DENSITY_THRESHOLD = 5  # events/min
    HIGH_DENSITY_THRESHOLD = 100  # events/min
    SPIKE_DENSITY_THRESHOLD = 500  # events/min

    # Cost constants (configurable)
    DBU_COST_SERVERLESS = 0.55  # $/DBU for serverless
    DBU_COST_CLASSIC = 0.22  # $/DBU for classic compute
    EVENT_COST_ESTIMATE = 0.0001  # Estimated cost per event processing

    # Billing meter configuration
    DEFAULT_METER_NAME = "resonance_meaningful_events"

    def __init__(
        self,
        stripe_api_key: str | None = None,
        databricks_client: Any | None = None,
        meter_event_callback: Callable[[BillingMeterEvent], bool] | None = None,
        cost_tier: CostTier = CostTier.STANDARD,
    ):
        """
        Initialize Cost Optimizer.

        Args:
            stripe_api_key: Stripe API key for billing integration
            databricks_client: Databricks WorkspaceClient instance
            meter_event_callback: Callback to send meter events (for testing)
            cost_tier: Customer's cost tier for pricing
        """
        self._stripe_api_key = stripe_api_key
        self._databricks_client = databricks_client
        self._meter_callback = meter_event_callback or self._default_meter_callback
        self._cost_tier = cost_tier

        # Current allocation
        self._allocation = ResourceAllocation(
            tick_rate_hz=60.0,
            batch_size=100,
            worker_count=4,
            queue_depth=1000,
            compute_mode=ComputeMode.HYBRID,
            dbu_limit_per_hour=10.0,
        )

        # Tracking
        self._current_period_start = datetime.now(UTC)
        self._cost_history: list[CostMetrics] = []
        self._pending_meter_events: list[BillingMeterEvent] = []
        self._event_density_buffer: list[tuple[datetime, int]] = []
        self._optimization_recommendations: list[OptimizationRecommendation] = []

        # Running state
        self._is_running = False
        self._optimization_task: asyncio.Task | None = None
        self._meter_flush_task: asyncio.Task | None = None

        logger.info(f"CostOptimizer initialized with tier: {cost_tier.value}")

    def _default_meter_callback(self, event: BillingMeterEvent) -> bool:
        """Default meter callback - logs event (no actual Stripe call)."""
        logger.info(f"[DRY RUN] Stripe meter event: {event.event_name} = {event.value}")
        return True

    # ─────────────────────────────────────────────────────────────────────────
    # Adaptive Tick-Rate Adjustment
    # ─────────────────────────────────────────────────────────────────────────

    def record_event_density(self, events_count: int) -> None:
        """Record current event density for adaptive adjustment."""
        now = datetime.now(UTC)
        self._event_density_buffer.append((now, events_count))

        # Keep only last 10 minutes of data
        cutoff = now - timedelta(minutes=10)
        self._event_density_buffer = [(ts, count) for ts, count in self._event_density_buffer if ts > cutoff]

    def get_current_event_density(self) -> float:
        """Calculate current events per minute."""
        if len(self._event_density_buffer) < 2:
            return 0.0

        now = datetime.now(UTC)
        cutoff = now - timedelta(minutes=1)
        recent = [count for ts, count in self._event_density_buffer if ts > cutoff]
        return sum(recent)

    def calculate_optimal_tick_rate(self) -> float:
        """
        Calculate optimal tick rate based on event density.

        Returns:
            Optimal tick rate in Hz (10-120)
        """
        density = self.get_current_event_density()

        if density < self.LOW_DENSITY_THRESHOLD:
            # Low traffic: reduce tick rate to save resources
            return max(10.0, 20.0)
        elif density < self.HIGH_DENSITY_THRESHOLD:
            # Normal traffic: standard tick rate
            return 60.0
        elif density < self.SPIKE_DENSITY_THRESHOLD:
            # High traffic: increase tick rate
            return 90.0
        else:
            # Spike: maximum tick rate
            return 120.0

    def apply_tick_rate_adjustment(self) -> bool:
        """Apply optimal tick rate if significantly different from current."""
        optimal = self.calculate_optimal_tick_rate()
        current = self._allocation.tick_rate_hz

        # Only adjust if difference > 20%
        if abs(optimal - current) / current > 0.2:
            old_rate = current
            self._allocation.tick_rate_hz = optimal
            logger.info(f"Tick rate adjusted: {old_rate:.1f}Hz → {optimal:.1f}Hz")
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # Smart Batching
    # ─────────────────────────────────────────────────────────────────────────

    def calculate_optimal_batch_size(self) -> int:
        """
        Calculate optimal batch size based on density and cost.

        Returns:
            Optimal batch size (10-1000)
        """
        density = self.get_current_event_density()

        if density < self.LOW_DENSITY_THRESHOLD:
            # Low density: smaller batches for lower latency
            return 25
        elif density < self.HIGH_DENSITY_THRESHOLD:
            # Normal: moderate batch size
            return 100
        elif density < self.SPIKE_DENSITY_THRESHOLD:
            # High density: larger batches for efficiency
            return 250
        else:
            # Spike: maximum batch size
            return 500

    def apply_batch_size_adjustment(self) -> bool:
        """Apply optimal batch size if different from current."""
        optimal = self.calculate_optimal_batch_size()
        current = self._allocation.batch_size

        if optimal != current:
            self._allocation.batch_size = optimal
            logger.info(f"Batch size adjusted: {current} → {optimal}")
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # Compute Mode Optimization
    # ─────────────────────────────────────────────────────────────────────────

    def calculate_optimal_compute_mode(self) -> ComputeMode:
        """
        Determine optimal compute mode based on usage patterns.

        Serverless: Fast start, higher $/DBU - good for spiky workloads
        Classic: Slow start, lower $/DBU - good for sustained workloads
        Hybrid: Auto-switching based on load

        Returns:
            Optimal compute mode
        """
        density = self.get_current_event_density()

        # Check for sustained high load (favor Classic)
        sustained_high = len(self._event_density_buffer) >= 5 and all(
            count > self.HIGH_DENSITY_THRESHOLD for _, count in self._event_density_buffer[-5:]
        )

        if sustained_high:
            return ComputeMode.CLASSIC

        # Check for spiky pattern (favor Serverless)
        if density > self.SPIKE_DENSITY_THRESHOLD:
            return ComputeMode.SERVERLESS

        # Default to hybrid
        return ComputeMode.HYBRID

    def get_dbu_cost_rate(self) -> float:
        """Get current DBU cost rate based on compute mode."""
        mode = self._allocation.compute_mode
        if mode == ComputeMode.SERVERLESS:
            return self.DBU_COST_SERVERLESS
        elif mode == ComputeMode.CLASSIC:
            return self.DBU_COST_CLASSIC
        else:  # Hybrid - weighted average
            return (self.DBU_COST_SERVERLESS + self.DBU_COST_CLASSIC) / 2

    # ─────────────────────────────────────────────────────────────────────────
    # Cost Tracking
    # ─────────────────────────────────────────────────────────────────────────

    def create_cost_period(self) -> CostMetrics:
        """Create a new cost tracking period."""
        now = datetime.now(UTC)
        return CostMetrics(
            period_start=now,
            period_end=now + timedelta(hours=1),
        )

    def record_event_cost(
        self,
        event_count: int,
        high_impact_count: int,
        meaningful_count: int,
        dbu_consumed: float = 0.0,
    ) -> CostMetrics:
        """
        Record event processing costs.

        Args:
            event_count: Total events processed
            high_impact_count: Events with impact >= threshold
            meaningful_count: Events that generated insights
            dbu_consumed: DBUs consumed for this batch

        Returns:
            Updated cost metrics
        """
        if not self._cost_history or datetime.now(UTC) > self._cost_history[-1].period_end:
            self._cost_history.append(self.create_cost_period())

        metrics = self._cost_history[-1]
        metrics.total_events += event_count
        metrics.high_impact_events += high_impact_count
        metrics.meaningful_events += meaningful_count
        metrics.low_impact_events += event_count - high_impact_count
        metrics.dbu_consumed += dbu_consumed

        # Calculate costs
        dbu_cost = dbu_consumed * self.get_dbu_cost_rate()
        processing_cost = event_count * self.EVENT_COST_ESTIMATE
        metrics.cost_usd += dbu_cost + processing_cost

        metrics.calculate_derived()

        return metrics

    def get_current_cost_metrics(self) -> CostMetrics | None:
        """Get current period metrics."""
        return self._cost_history[-1] if self._cost_history else None

    def get_cost_history(self, periods: int = 24) -> list[CostMetrics]:
        """Get cost history for the last N periods."""
        return self._cost_history[-periods:]

    # ─────────────────────────────────────────────────────────────────────────
    # Stripe Billing Integration
    # ─────────────────────────────────────────────────────────────────────────

    def queue_meter_event(
        self,
        customer_id: str,
        event_name: str,
        value: int,
        metadata: dict[str, Any] | None = None,
    ) -> BillingMeterEvent:
        """
        Queue a billing meter event for Stripe.

        Args:
            customer_id: Stripe customer ID
            event_name: Name of the meter (e.g., "resonance_meaningful_events")
            value: Usage value to record
            metadata: Additional metadata

        Returns:
            Created meter event
        """
        event = BillingMeterEvent(
            id=f"evt_{uuid4().hex[:12]}",
            event_name=event_name,
            customer_id=customer_id,
            value=value,
            timestamp=datetime.now(UTC),
            metadata=metadata or {},
        )
        self._pending_meter_events.append(event)
        logger.debug(f"Queued meter event: {event_name}={value} for {customer_id}")
        return event

    async def flush_meter_events(self) -> int:
        """
        Send all pending meter events to Stripe.

        Returns:
            Number of events successfully sent
        """
        sent_count = 0
        events_to_send = self._pending_meter_events.copy()
        self._pending_meter_events.clear()

        for event in events_to_send:
            try:
                success = self._meter_callback(event)
                if success:
                    event.sent = True
                    event.sent_at = datetime.now(UTC)
                    sent_count += 1

                    # Update cost metrics
                    if self._cost_history:
                        self._cost_history[-1].stripe_meter_events_sent += 1
                else:
                    # Re-queue failed events
                    self._pending_meter_events.append(event)
            except Exception as e:
                logger.error(f"Failed to send meter event {event.id}: {e}")
                self._pending_meter_events.append(event)

        if sent_count > 0:
            logger.info(f"Flushed {sent_count} meter events to Stripe")

        return sent_count

    def create_stripe_meter_event_payload(
        self,
        customer_id: str,
        meaningful_events: int,
    ) -> dict[str, Any]:
        """
        Create Stripe API payload for meter event.

        This is the format expected by:
        POST /v1/billing/meter_events

        Args:
            customer_id: Stripe customer ID
            meaningful_events: Count of meaningful events

        Returns:
            API-ready payload dict
        """
        return {
            "event_name": self.DEFAULT_METER_NAME,
            "payload": {
                "stripe_customer_id": customer_id,
                "value": str(meaningful_events),
            },
            "identifier": f"res_{uuid4().hex[:12]}",
            "timestamp": int(datetime.now(UTC).timestamp()),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Optimization Analysis
    # ─────────────────────────────────────────────────────────────────────────

    def analyze_and_recommend(self) -> list[OptimizationRecommendation]:
        """
        Analyze current state and generate optimization recommendations.

        Returns:
            List of optimization recommendations
        """
        recommendations: list[OptimizationRecommendation] = []

        # Check tick rate
        optimal_tick = self.calculate_optimal_tick_rate()
        if abs(optimal_tick - self._allocation.tick_rate_hz) > 10:
            savings = abs(optimal_tick - self._allocation.tick_rate_hz) / 120 * 15
            recommendations.append(
                OptimizationRecommendation(
                    id=f"OPT-{uuid4().hex[:8].upper()}",
                    category="tick_rate",
                    current_value=self._allocation.tick_rate_hz,
                    recommended_value=optimal_tick,
                    expected_savings_pct=savings,
                    rationale=f"Event density suggests {'lower' if optimal_tick < self._allocation.tick_rate_hz else 'higher'} tick rate for optimal cost-performance.",
                    confidence=0.8,
                )
            )

        # Check batch size
        optimal_batch = self.calculate_optimal_batch_size()
        if optimal_batch != self._allocation.batch_size:
            savings = 10.0 if optimal_batch > self._allocation.batch_size else 5.0
            recommendations.append(
                OptimizationRecommendation(
                    id=f"OPT-{uuid4().hex[:8].upper()}",
                    category="batching",
                    current_value=self._allocation.batch_size,
                    recommended_value=optimal_batch,
                    expected_savings_pct=savings,
                    rationale=f"{'Larger' if optimal_batch > self._allocation.batch_size else 'Smaller'} batches would {'reduce overhead' if optimal_batch > self._allocation.batch_size else 'improve latency'}.",
                    confidence=0.75,
                )
            )

        # Check compute mode
        optimal_mode = self.calculate_optimal_compute_mode()
        if optimal_mode != self._allocation.compute_mode:
            if optimal_mode == ComputeMode.CLASSIC:
                savings = 50.0  # Classic is ~60% cheaper per DBU
            elif optimal_mode == ComputeMode.SERVERLESS:
                savings = -20.0  # More expensive but faster
            else:
                savings = 10.0

            recommendations.append(
                OptimizationRecommendation(
                    id=f"OPT-{uuid4().hex[:8].upper()}",
                    category="compute_mode",
                    current_value=self._allocation.compute_mode.value,
                    recommended_value=optimal_mode.value,
                    expected_savings_pct=savings,
                    rationale=f"Current workload pattern suits {optimal_mode.value} compute.",
                    confidence=0.7,
                )
            )

        self._optimization_recommendations = recommendations
        return recommendations

    def get_current_allocation(self) -> ResourceAllocation:
        """Get current resource allocation."""
        return self._allocation

    def get_pending_recommendations(self) -> list[OptimizationRecommendation]:
        """Get pending optimization recommendations."""
        return self._optimization_recommendations

    # ─────────────────────────────────────────────────────────────────────────
    # Service Lifecycle
    # ─────────────────────────────────────────────────────────────────────────

    async def start(self, optimization_interval: float = 60.0) -> None:
        """Start the cost optimizer background tasks."""
        if self._is_running:
            logger.warning("CostOptimizer already running")
            return

        self._is_running = True

        async def optimization_loop():
            while self._is_running:
                try:
                    self.apply_tick_rate_adjustment()
                    self.apply_batch_size_adjustment()
                    self.analyze_and_recommend()
                except Exception as e:
                    logger.error(f"Optimization loop error: {e}")
                await asyncio.sleep(optimization_interval)

        async def meter_flush_loop():
            while self._is_running:
                try:
                    await self.flush_meter_events()
                except Exception as e:
                    logger.error(f"Meter flush error: {e}")
                await asyncio.sleep(30.0)  # Flush every 30 seconds

        self._optimization_task = asyncio.create_task(optimization_loop())
        self._meter_flush_task = asyncio.create_task(meter_flush_loop())

        logger.info("CostOptimizer started")

    async def stop(self) -> None:
        """Stop the cost optimizer."""
        self._is_running = False

        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass

        if self._meter_flush_task:
            self._meter_flush_task.cancel()
            try:
                await self._meter_flush_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self.flush_meter_events()

        logger.info("CostOptimizer stopped")
