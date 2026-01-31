"""
Billing service.

Service for managing billing cycles, invoices, and subscription billing.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from ...config import get_settings
from ...models.payment import Invoice, Subscription, SubscriptionTier
from ...repositories.payment import InvoiceRepository, SubscriptionRepository
from ...repositories.usage import UsageRepository
from .meter import UsageMeter

logger = logging.getLogger(__name__)


class BillingService:
    """Service for billing operations."""

    def __init__(
        self,
        subscription_repo: SubscriptionRepository | None = None,
        invoice_repo: InvoiceRepository | None = None,
        usage_repo: UsageRepository | None = None,
        usage_meter: UsageMeter | None = None,
    ):
        """
        Initialize billing service.

        Args:
            subscription_repo: Subscription repository
            invoice_repo: Invoice repository
            usage_repo: Usage repository
            usage_meter: Usage meter service
        """
        from ...repositories.payment import InvoiceRepository, SubscriptionRepository
        from ...repositories.usage import UsageRepository

        self.subscription_repo = subscription_repo or SubscriptionRepository()
        self.invoice_repo = invoice_repo or InvoiceRepository()
        self.usage_repo = usage_repo or UsageRepository()
        self.usage_meter = usage_meter or UsageMeter(self.usage_repo)
        self.settings = get_settings()

    async def get_user_subscription(self, user_id: str) -> Subscription | None:
        """
        Get active subscription for a user.

        Args:
            user_id: User identifier

        Returns:
            Active subscription or None
        """
        return await self.subscription_repo.get_active_by_user(user_id)

    async def get_user_tier(self, user_id: str) -> SubscriptionTier:
        """
        Get subscription tier for a user.

        Args:
            user_id: User identifier

        Returns:
            Subscription tier (defaults to FREE if no subscription)
        """
        subscription = await self.get_user_subscription(user_id)
        if subscription and subscription.is_active():
            return subscription.tier
        return SubscriptionTier.FREE

    async def generate_invoice(self, user_id: str, subscription_id: str | None = None) -> Invoice:
        """
        Generate an invoice for a user's usage.

        Args:
            user_id: User identifier
            subscription_id: Optional subscription ID

        Returns:
            Generated invoice
        """
        import uuid

        subscription = (
            await self.subscription_repo.get(subscription_id)
            if subscription_id
            else await self.get_user_subscription(user_id)
        )

        # Calculate billing period

        now = datetime.now(UTC)
        period_start = subscription.current_period_start if subscription else now - timedelta(days=30)
        period_end = subscription.current_period_end if subscription else now

        # Get usage for period
        await self.usage_repo.get_by_user(user_id, start_date=period_start, end_date=period_end)

        # Calculate charges
        tier = subscription.tier if subscription else SubscriptionTier.FREE
        base_amount = 0

        if tier == SubscriptionTier.STARTER:
            base_amount = self.settings.billing.starter_monthly_price
        elif tier == SubscriptionTier.PROFESSIONAL:
            base_amount = self.settings.billing.pro_monthly_price

        # Calculate overage
        limits = await self.usage_meter.get_tier_limits(tier)
        usage_records = await self.usage_repo.get_by_user(user_id, start_date=period_start, end_date=period_end)

        # Calculate usage by endpoint type
        usage_by_type = {}
        for record in usage_records:
            endpoint_type = self._map_endpoint_to_type(record.endpoint)
            usage_by_type[endpoint_type] = usage_by_type.get(endpoint_type, 0) + record.cost_units

        # Calculate overage charges
        overage_amount = 0
        overage_line_items = []

        for usage_type, usage_units in usage_by_type.items():
            limit = limits.get(usage_type, 0)
            if usage_units > limit:
                overage_units = usage_units - limit
                overage_cost_cents = overage_units * self._get_overage_cost_cents(usage_type)
                overage_amount += overage_cost_cents

                overage_line_items.append({
                    "description": f"Overage: {usage_type.replace('_', ' ').title()} ({overage_units} units)",
                    "amount_cents": overage_cost_cents,
                    "usage_type": usage_type,
                    "units_used": usage_units,
                    "limit": limit,
                    "overage_units": overage_units
                })

        total_amount = base_amount + overage_amount

        # Create invoice
        # Create line items
        line_items = []

        # Add base subscription charge if applicable
        if base_amount > 0:
            line_items.append({
                "description": f"{tier.value.title()} subscription",
                "amount_cents": base_amount,
                "type": "subscription"
            })

        # Add overage charges
        line_items.extend(overage_line_items)

        # Create invoice
        invoice = Invoice(
            id=str(uuid.uuid4()),
            user_id=user_id,
            subscription_id=subscription.id if subscription else None,
            amount_cents=total_amount,
            currency=self.settings.payment.currency.upper(),
            status="draft",
            period_start=period_start,
            period_end=period_end,
            due_date=now + timedelta(days=14),
            line_items=line_items,
        )

        await self.invoice_repo.add(invoice)
        return invoice

    def _map_endpoint_to_type(self, endpoint: str) -> str:
        """
        Map endpoint path to usage type for billing.

        Args:
            endpoint: API endpoint path

        Returns:
            Usage type string (relationship_analysis, entity_extraction, etc.)
        """
        if "relationship" in endpoint:
            return "relationship_analysis"
        elif "entity" in endpoint or "ner" in endpoint:
            return "entity_extraction"
        elif "batch" in endpoint:
            return "batch_analysis"
        elif "scenario" in endpoint:
            return "scenario_analysis"
        else:
            return "entity_extraction"  # Default

    def _get_overage_cost_cents(self, usage_type: str) -> int:
        """
        Get overage cost per unit for a usage type.

        Args:
            usage_type: Usage type string

        Returns:
            Cost in cents per unit
        """
        billing_settings = self.settings.billing

        if usage_type == "relationship_analysis":
            return billing_settings.relationship_analysis_overage_cents
        elif usage_type == "entity_extraction":
            return billing_settings.entity_extraction_overage_cents
        elif usage_type == "batch_analysis":
            return billing_settings.relationship_analysis_overage_cents * 10  # Batch costs more
        elif usage_type == "scenario_analysis":
            return billing_settings.relationship_analysis_overage_cents * 5  # Scenario costs medium
        else:
            return billing_settings.entity_extraction_overage_cents  # Default

    async def get_usage_summary(self, user_id: str, period_days: int = 30) -> dict[str, Any]:
        """
        Get usage summary for a user.

        Args:
            user_id: User identifier
            period_days: Period to summarize

        Returns:
            Usage summary dictionary
        """
        tier = await self.get_user_tier(user_id)
        limits = await self.usage_meter.get_tier_limits(tier)
        usage = await self.usage_repo.get_total_usage(user_id, period_days)

        return {
            "tier": tier.value,
            "period_days": period_days,
            "usage": usage,
            "limits": limits,
        }
