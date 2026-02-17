"""
Stripe Billing Integration - Phase 3 Implementation.

Provides:
- Usage-based billing via Billing Meters API
- Meter event creation and management
- Cost tracking per customer
- Invoice preview for current usage
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes", "y", "on"}


def _is_production_environment() -> bool:
    env = (
        os.getenv("MOTHERSHIP_ENVIRONMENT")
        or os.getenv("GRID_ENVIRONMENT")
        or os.getenv("ENVIRONMENT")
        or os.getenv("ENV")
        or "development"
    )
    return env.strip().lower() in {"production", "prod"}


class CostTier(StrEnum):
    """Cost tiers for usage-based billing."""

    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


# Environment check
STRIPE_ENABLED = bool(os.getenv("STRIPE_API_KEY", ""))


@dataclass
class MeterEvent:
    """Stripe Meter Event representation with explicit degradation tracking.

    Following the "Explicit Result" pattern - includes degraded flag to indicate
    when this event is in dry-run/mock mode vs live Stripe API.
    """

    id: str
    event_name: str
    customer_id: str
    value: int
    timestamp: datetime
    identifier: str
    livemode: bool = False
    created: datetime | None = None
    origin: str = "pending"
    degraded: bool = False  # True if this is a dry-run/mock event, not sent to Stripe


@dataclass
class MeterSummary:
    """Summary of meter usage for a customer with explicit degradation tracking."""

    meter_id: str
    meter_name: str
    customer_id: str
    start_time: datetime
    end_time: datetime
    aggregated_value: int
    origin: str = "live"
    degraded: bool = False  # True if summary is from local tracking, not live API


@dataclass
class InvoicePreview:
    """Preview of upcoming invoice with explicit degradation tracking."""

    customer_id: str
    amount_due: float
    currency: str
    period_start: datetime
    period_end: datetime
    line_items: list[dict[str, Any]] = field(default_factory=list)
    origin: str = "live"
    degraded: bool = False  # True if preview is calculated locally, not from Stripe


class StripeBilling:
    """
    Stripe Billing Integration for Usage-Based Pricing.

    Implements billing integration using Stripe's Billing Meters API:
    - Send meter events for each meaningful Resonance event
    - Query aggregated usage summaries
    - Preview upcoming invoices

    Meter Configuration:
        - event_name: "resonance_meaningful_events"
        - aggregation: SUM
        - value: count of meaningful events

    Authentication:
        Set STRIPE_API_KEY environment variable
    """

    # Default meter names
    METER_MEANINGFUL_EVENTS = "resonance_meaningful_events"
    METER_HIGH_IMPACT_EVENTS = "resonance_high_impact_events"
    METER_API_CALLS = "resonance_api_calls"

    def __init__(
        self,
        api_key: str | None = None,
        meter_event_callback: Callable | None = None,
        cost_tier: CostTier = CostTier.STANDARD,
        allow_dry_run_in_production: bool | None = None,
    ):
        """
        Initialize Stripe Billing.

        Args:
            api_key: Stripe API key (or use STRIPE_API_KEY env var)
            meter_event_callback: Custom callback for meter events (testing)
        """
        self._api_key = api_key or os.getenv("STRIPE_API_KEY", "")
        self._meter_callback = meter_event_callback
        self._cost_tier = cost_tier
        self._allow_dry_run_in_production = (
            allow_dry_run_in_production
            if allow_dry_run_in_production is not None
            else _parse_bool(os.getenv("STRIPE_BILLING_ALLOW_DRY_RUN_IN_PRODUCTION"), False)
        )

        # Client state
        self._stripe: Any = None
        self._is_initialized = False

        # Tracking
        self._events_sent: list[MeterEvent] = []
        self._pending_events: list[MeterEvent] = []
        self._customer_usage: dict[str, int] = {}  # customer_id -> total usage

        if self._api_key:
            initialized = self._initialize_client()
            if not initialized and _is_production_environment() and not self._allow_dry_run_in_production:
                raise RuntimeError(
                    "StripeBilling failed to initialize Stripe in production. "
                    "Set STRIPE_API_KEY correctly or explicitly allow dry-run mode with "
                    "STRIPE_BILLING_ALLOW_DRY_RUN_IN_PRODUCTION=true."
                )
        else:
            if _is_production_environment() and not self._allow_dry_run_in_production and not self._meter_callback:
                raise RuntimeError(
                    "StripeBilling dry-run mode is forbidden in production. "
                    "Set STRIPE_API_KEY, provide a live meter_event_callback, or explicitly allow dry-run mode with "
                    "STRIPE_BILLING_ALLOW_DRY_RUN_IN_PRODUCTION=true."
                )
            logger.info("Stripe API key not set - billing in dry-run mode")

    def _initialize_client(self) -> bool:
        """Initialize the Stripe client."""
        try:
            import stripe

            stripe.api_key = self._api_key
            self._stripe = stripe
            self._is_initialized = True
            logger.info("Stripe client initialized")
            return True
        except ImportError:
            logger.error("stripe package not installed. Run: pip install stripe")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Stripe: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # Meter Event Management
    # ─────────────────────────────────────────────────────────────────────────

    def create_meter_event(
        self,
        customer_id: str,
        event_name: str,
        value: int,
        identifier: str | None = None,
        timestamp: datetime | None = None,
    ) -> MeterEvent:
        """
        Create a billing meter event.

        This corresponds to:
        POST /v1/billing/meter_events

        Args:
            customer_id: Stripe customer ID (cus_xxx)
            event_name: Name of the meter
            value: Usage value to record
            identifier: Unique identifier (auto-generated if not provided)
            timestamp: Event timestamp (defaults to now)

        Returns:
            Created MeterEvent
        """
        event = MeterEvent(
            id=f"evt_{uuid4().hex[:12]}",
            event_name=event_name,
            customer_id=customer_id,
            value=value,
            timestamp=timestamp or datetime.now(UTC),
            identifier=identifier or f"res_{uuid4().hex[:12]}",
        )

        self._pending_events.append(event)

        # Track usage
        if customer_id not in self._customer_usage:
            self._customer_usage[customer_id] = 0
        self._customer_usage[customer_id] += value

        logger.debug(f"Created meter event: {event_name}={value} for {customer_id}")
        return event

    def record_meaningful_events(
        self,
        customer_id: str,
        event_count: int,
    ) -> MeterEvent:
        """
        Record meaningful Resonance events for billing.

        Args:
            customer_id: Stripe customer ID
            event_count: Number of meaningful events

        Returns:
            Created MeterEvent
        """
        return self.create_meter_event(
            customer_id=customer_id,
            event_name=self.METER_MEANINGFUL_EVENTS,
            value=event_count,
        )

    def record_high_impact_events(
        self,
        customer_id: str,
        event_count: int,
    ) -> MeterEvent:
        """
        Record high-impact (spike) events for billing.

        Args:
            customer_id: Stripe customer ID
            event_count: Number of high-impact events

        Returns:
            Created MeterEvent
        """
        return self.create_meter_event(
            customer_id=customer_id,
            event_name=self.METER_HIGH_IMPACT_EVENTS,
            value=event_count,
        )

    async def send_pending_events(self) -> int:
        """
        Send all pending meter events to Stripe.

        Returns:
            Number of events successfully sent
        """
        if not self._pending_events:
            return 0

        sent_count = 0
        events_to_send = self._pending_events.copy()
        self._pending_events.clear()

        for event in events_to_send:
            try:
                if self._meter_callback:
                    # Use test callback
                    self._meter_callback(event)
                    sent_count += 1
                    event.created = datetime.now(UTC)
                    event.origin = "callback"
                    event.degraded = False  # Test callback is intentional, not degraded
                    self._events_sent.append(event)
                elif self._is_initialized and self._stripe:
                    # Send to Stripe API
                    response = self._stripe.billing.MeterEvent.create(
                        event_name=event.event_name,
                        payload={
                            "stripe_customer_id": event.customer_id,
                            "value": str(event.value),
                        },
                        identifier=event.identifier,
                        timestamp=int(event.timestamp.timestamp()),
                    )
                    event.created = datetime.now(UTC)
                    event.livemode = response.get("livemode", False)
                    event.origin = "live"
                    event.degraded = False  # Real Stripe API call
                    self._events_sent.append(event)
                    sent_count += 1
                else:
                    # Dry run mode - explicitly mark as degraded
                    logger.info(f"[DRY RUN] Stripe meter event: {event.event_name}={event.value}")
                    event.created = datetime.now(UTC)
                    event.origin = "dry_run"
                    event.degraded = True  # Dry run is degraded - not sent to real API
                    self._events_sent.append(event)
                    sent_count += 1

            except Exception as e:
                logger.error(f"Failed to send meter event {event.id}: {e}")
                self._pending_events.append(event)  # Re-queue

        if sent_count > 0:
            logger.info(f"Sent {sent_count} meter events to Stripe")

        return sent_count

    # ─────────────────────────────────────────────────────────────────────────
    # Usage Queries
    # ─────────────────────────────────────────────────────────────────────────

    def get_customer_usage(self, customer_id: str) -> int:
        """Get total tracked usage for a customer."""
        return self._customer_usage.get(customer_id, 0)

    def get_all_customer_usage(self) -> dict[str, int]:
        """Get usage for all tracked customers."""
        return self._customer_usage.copy()

    async def get_meter_summary(
        self,
        customer_id: str,
        meter_name: str = METER_MEANINGFUL_EVENTS,
    ) -> MeterSummary:
        """
        Get aggregated meter summary for a customer.

        Args:
            customer_id: Stripe customer ID
            meter_name: Name of the meter to query

        Returns:
            MeterSummary if available
        """
        # Use local tracking when not initialized OR when using test callback
        if not self._is_initialized or self._meter_callback:
            value = self._customer_usage.get(customer_id, 0)
            origin = "callback" if self._meter_callback else "dry_run"
            # Degraded when not using live Stripe API
            is_degraded = not self._is_initialized or self._meter_callback is None
            return MeterSummary(
                meter_id="local",
                meter_name=meter_name,
                customer_id=customer_id,
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
                aggregated_value=value,
                origin=origin,
                degraded=is_degraded,
            )

        try:
            # Query Stripe API for meter summary
            # Note: This requires listing meters and then querying summaries
            meters = self._stripe.billing.Meter.list(limit=10)

            for meter in meters.get("data", []):
                if meter.get("event_name") == meter_name:
                    # Get summary for this meter
                    summaries = self._stripe.billing.Meter.list_event_summaries(
                        meter.id,
                        customer=customer_id,
                    )
                    if summaries.get("data"):
                        s = summaries["data"][0]
                        return MeterSummary(
                            meter_id=meter.id,
                            meter_name=meter_name,
                            customer_id=customer_id,
                            start_time=datetime.fromtimestamp(s.get("start_time", 0), UTC),
                            end_time=datetime.fromtimestamp(s.get("end_time", 0), UTC),
                            aggregated_value=s.get("aggregated_value", 0),
                            origin="live",
                            degraded=False,  # Real Stripe API response
                        )
            # No meter found - return degraded result
            return MeterSummary(
                meter_id="not_found",
                meter_name=meter_name,
                customer_id=customer_id,
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
                aggregated_value=0,
                origin="not_found",
                degraded=True,
            )

        except Exception as e:
            logger.error(f"Failed to get meter summary: {e}")
            return MeterSummary(
                meter_id="error",
                meter_name=meter_name,
                customer_id=customer_id,
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
                aggregated_value=0,
                origin="error",
                degraded=True,
            )

    async def get_upcoming_invoice(
        self,
        customer_id: str,
    ) -> InvoicePreview:
        """
        Get preview of upcoming invoice for a customer.

        Args:
            customer_id: Stripe customer ID

        Returns:
            InvoicePreview if available
        """
        # Use local tracking when not initialized OR when using test callback
        if not self._is_initialized or self._meter_callback:
            origin = "callback" if self._meter_callback else "dry_run"
            # Logic for overage calculation in dry-run/test mode
            from application.mothership.config import get_settings

            settings = get_settings().billing
            usage = self._customer_usage.get(customer_id, 0)

            # Determine limits based on tier
            if self._cost_tier == CostTier.FREE:
                limit = settings.free_tier_resonance_events
                overage_rate = settings.resonance_event_overage_cents / 100
                base_price = 0
            elif self._cost_tier == CostTier.PREMIUM:
                limit = settings.pro_tier_resonance_events
                overage_rate = settings.resonance_event_overage_cents / 500  # Lower overage for premium
                base_price = settings.pro_monthly_price / 100
            else:  # STANDARD
                limit = settings.starter_tier_resonance_events
                overage_rate = settings.resonance_event_overage_cents / 100
                base_price = settings.starter_monthly_price / 100

            # Calculate overage
            overage_count = max(0, usage - limit)
            overage_amount = overage_count * overage_rate
            total_amount = base_price + overage_amount

            line_items = [
                {
                    "description": f"Subscription Base ({self._cost_tier.value})",
                    "quantity": 1,
                    "unit_amount": base_price,
                    "amount": base_price,
                }
            ]

            if overage_count > 0:
                line_items.append(
                    {
                        "description": "Resonance Events Overage",
                        "quantity": overage_count,
                        "unit_amount": overage_rate,
                        "amount": overage_amount,
                    }
                )

            return InvoicePreview(
                customer_id=customer_id,
                amount_due=total_amount,
                currency="usd",
                period_start=datetime.now(UTC),
                period_end=datetime.now(UTC),
                line_items=line_items,
                origin=origin,
            )

        try:
            invoice = self._stripe.Invoice.upcoming(customer=customer_id)

            line_items = []
            for item in invoice.get("lines", {}).get("data", []):
                line_items.append(
                    {
                        "description": item.get("description", ""),
                        "quantity": item.get("quantity", 0),
                        "unit_amount": item.get("unit_amount", 0) / 100,  # Convert cents
                        "amount": item.get("amount", 0) / 100,
                    }
                )

            return InvoicePreview(
                customer_id=customer_id,
                amount_due=invoice.get("amount_due", 0) / 100,
                currency=invoice.get("currency", "usd"),
                period_start=datetime.fromtimestamp(invoice.get("period_start", 0), UTC),
                period_end=datetime.fromtimestamp(invoice.get("period_end", 0), UTC),
                line_items=line_items,
                origin="live",
            )

        except Exception as e:
            logger.error(f"Failed to get upcoming invoice: {e}")
            return InvoicePreview(
                customer_id=customer_id,
                amount_due=0.0,
                currency="usd",
                period_start=datetime.now(UTC),
                period_end=datetime.now(UTC),
                origin="error",
                degraded=True,
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Statistics & Tracking
    # ─────────────────────────────────────────────────────────────────────────

    def get_events_sent(self, limit: int = 100) -> list[MeterEvent]:
        """Get recently sent meter events."""
        return self._events_sent[-limit:]

    def get_pending_count(self) -> int:
        """Get count of pending meter events."""
        return len(self._pending_events)

    def get_billing_stats(self) -> dict[str, Any]:
        """Get billing integration statistics."""
        origin_counts = {"live": 0, "dry_run": 0, "callback": 0, "pending": 0}
        for event in self._events_sent:
            origin_counts[event.origin] = origin_counts.get(event.origin, 0) + 1

        return {
            "is_initialized": self._is_initialized,
            "events_sent": len(self._events_sent),
            "events_pending": len(self._pending_events),
            "customers_tracked": len(self._customer_usage),
            "total_usage": sum(self._customer_usage.values()),
            "events_sent_by_origin": origin_counts,
        }

    @property
    def is_enabled(self) -> bool:
        """Check if Stripe integration is enabled."""
        return self._is_initialized or bool(self._meter_callback)
