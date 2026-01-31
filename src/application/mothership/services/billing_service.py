"""Billing service with overage calculation.

Provides usage tracking, tier limit enforcement, and overage charge calculation
for GRID's subscription-based billing model.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from application.mothership.config import BillingSettings

logger = logging.getLogger(__name__)


class SubscriptionTier(str, Enum):
    """Subscription tiers."""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"


@dataclass
class UsageRecord:
    """Record of resource usage."""

    user_id: str
    resource_type: str  # "relationship_analysis", "entity_extraction"
    quantity: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TierLimits:
    """Usage limits for a subscription tier."""

    relationship_analyses: int
    entity_extractions: int


@dataclass
class OverageCharges:
    """Calculated overage charges."""

    relationship_analysis_count: int = 0
    relationship_analysis_cost_cents: int = 0
    entity_extraction_count: int = 0
    entity_extraction_cost_cents: int = 0
    total_overage_cents: int = 0
    total_overage_dollars: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "relationship_analysis_count": self.relationship_analysis_count,
            "relationship_analysis_cost": f"${self.relationship_analysis_cost_cents / 100:.2f}",
            "entity_extraction_count": self.entity_extraction_count,
            "entity_extraction_cost": f"${self.entity_extraction_cost_cents / 100:.2f}",
            "total_overage": f"${self.total_overage_dollars:.2f}",
        }


@dataclass
class BillingSummary:
    """Complete billing summary for a user/organization."""

    tier: SubscriptionTier
    billing_period_start: datetime
    billing_period_end: datetime
    base_cost_cents: int
    usage: dict[str, int]  # resource_type -> quantity used
    tier_limits: TierLimits
    overages: OverageCharges
    total_due_cents: int
    total_due_dollars: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tier": self.tier.value,
            "billing_period": {
                "start": self.billing_period_start.isoformat(),
                "end": self.billing_period_end.isoformat(),
            },
            "base_cost": f"${self.base_cost_cents / 100:.2f}",
            "usage": self.usage,
            "tier_limits": {
                "relationship_analyses": self.tier_limits.relationship_analyses,
                "entity_extractions": self.tier_limits.entity_extractions,
            },
            "overages": self.overages.to_dict(),
            "total_due": f"${self.total_due_dollars:.2f}",
        }


class BillingService:
    """Billing service for usage tracking and overage calculation.

    Tracks usage against tier limits and calculates overage charges.
    """

    def __init__(self, settings: BillingSettings | None = None):
        """Initialize billing service.

        Args:
            settings: Billing settings (loads from env if None)
        """
        self._settings = settings or BillingSettings.from_env()
        self._usage_store: dict[str, list[UsageRecord]] = {}  # user_id -> usage records

    def _get_tier_limits(self, tier: SubscriptionTier) -> TierLimits:
        """Get usage limits for a tier."""
        limits = {
            SubscriptionTier.FREE: TierLimits(
                relationship_analyses=self._settings.free_tier_relationship_analyses,
                entity_extractions=self._settings.free_tier_entity_extractions,
            ),
            SubscriptionTier.STARTER: TierLimits(
                relationship_analyses=self._settings.starter_tier_relationship_analyses,
                entity_extractions=self._settings.starter_tier_entity_extractions,
            ),
            SubscriptionTier.PRO: TierLimits(
                relationship_analyses=self._settings.pro_tier_relationship_analyses,
                entity_extractions=self._settings.pro_tier_entity_extractions,
            ),
        }
        return limits.get(tier, limits[SubscriptionTier.FREE])

    def _get_base_cost(self, tier: SubscriptionTier) -> int:
        """Get base monthly cost for a tier (in cents)."""
        costs = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.STARTER: self._settings.starter_monthly_price,
            SubscriptionTier.PRO: self._settings.pro_monthly_price,
        }
        return costs.get(tier, 0)

    async def record_usage(
        self,
        user_id: str,
        resource_type: str,
        quantity: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record usage for a user.

        Args:
            user_id: User identifier
            resource_type: Type of resource used
            quantity: Amount used
            metadata: Additional metadata
        """
        record = UsageRecord(
            user_id=user_id,
            resource_type=resource_type,
            quantity=quantity,
            metadata=metadata or {},
        )

        if user_id not in self._usage_store:
            self._usage_store[user_id] = []

        self._usage_store[user_id].append(record)
        logger.debug(f"Recorded usage: {user_id} used {quantity} {resource_type}")

    async def get_usage(
        self,
        user_id: str,
        resource_type: str | None = None,
        since: datetime | None = None,
    ) -> int:
        """Get total usage for a user.

        Args:
            user_id: User identifier
            resource_type: Filter by resource type (optional)
            since: Get usage since this date (optional)

        Returns:
            Total usage quantity
        """
        records = self._usage_store.get(user_id, [])

        total = 0
        for record in records:
            if resource_type and record.resource_type != resource_type:
                continue
            if since and record.timestamp < since:
                continue
            total += record.quantity

        return total

    def calculate_overage(
        self,
        tier: SubscriptionTier,
        relationship_analysis_usage: int,
        entity_extraction_usage: int,
    ) -> OverageCharges:
        """Calculate overage charges based on usage vs tier limits.

        Args:
            tier: Subscription tier
            relationship_analysis_usage: Number of relationship analyses used
            entity_extraction_usage: Number of entity extractions used

        Returns:
            OverageCharges with calculated costs
        """
        limits = self._get_tier_limits(tier)
        charges = OverageCharges()

        # Calculate relationship analysis overage
        if relationship_analysis_usage > limits.relationship_analyses:
            charges.relationship_analysis_count = (
                relationship_analysis_usage - limits.relationship_analyses
            )
            charges.relationship_analysis_cost_cents = (
                charges.relationship_analysis_count
                * self._settings.relationship_analysis_overage_cents
            )

        # Calculate entity extraction overage
        if entity_extraction_usage > limits.entity_extractions:
            charges.entity_extraction_count = (
                entity_extraction_usage - limits.entity_extractions
            )
            charges.entity_extraction_cost_cents = (
                charges.entity_extraction_count
                * self._settings.entity_extraction_overage_cents
            )

        # Calculate totals
        charges.total_overage_cents = (
            charges.relationship_analysis_cost_cents + charges.entity_extraction_cost_cents
        )
        charges.total_overage_dollars = charges.total_overage_cents / 100

        logger.info(
            f"Overage calculation for {tier.value}: "
            f"${charges.total_overage_dollars:.2f} "
            f"({charges.relationship_analysis_count} relationship analyses, "
            f"{charges.entity_extraction_count} entity extractions)"
        )

        return charges

    async def get_billing_summary(
        self,
        user_id: str,
        tier: SubscriptionTier,
        billing_period_start: datetime | None = None,
    ) -> BillingSummary:
        """Generate complete billing summary for a user.

        Args:
            user_id: User identifier
            tier: Subscription tier
            billing_period_start: Start of billing period (defaults to current cycle)

        Returns:
            BillingSummary with all charges
        """
        # Determine billing period
        if billing_period_start is None:
            # Default to start of current cycle (30 days ago)
            billing_period_start = datetime.now(UTC) - timedelta(
                days=self._settings.billing_cycle_days
            )

        billing_period_end = billing_period_start + timedelta(
            days=self._settings.billing_cycle_days
        )

        # Get usage for period
        relationship_usage = await self.get_usage(
            user_id, "relationship_analysis", since=billing_period_start
        )
        entity_usage = await self.get_usage(
            user_id, "entity_extraction", since=billing_period_start
        )

        usage = {
            "relationship_analyses": relationship_usage,
            "entity_extractions": entity_usage,
        }

        # Get tier limits and base cost
        tier_limits = self._get_tier_limits(tier)
        base_cost = self._get_base_cost(tier)

        # Calculate overages
        overages = self.calculate_overage(tier, relationship_usage, entity_usage)

        # Calculate total
        total_due_cents = base_cost + overages.total_overage_cents
        total_due_dollars = total_due_cents / 100

        return BillingSummary(
            tier=tier,
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
            base_cost_cents=base_cost,
            usage=usage,
            tier_limits=tier_limits,
            overages=overages,
            total_due_cents=total_due_cents,
            total_due_dollars=total_due_dollars,
        )

    async def check_limit_exceeded(
        self,
        user_id: str,
        tier: SubscriptionTier,
        resource_type: str,
    ) -> tuple[bool, int, int]:
        """Check if user has exceeded their tier limit for a resource.

        Args:
            user_id: User identifier
            tier: Subscription tier
            resource_type: Resource type to check

        Returns:
            Tuple of (limit_exceeded, current_usage, limit)
        """
        limits = self._get_tier_limits(tier)

        # Map resource type to limit
        limit_map = {
            "relationship_analysis": limits.relationship_analyses,
            "entity_extraction": limits.entity_extractions,
        }

        limit = limit_map.get(resource_type, 0)

        # Get current usage for billing period
        period_start = datetime.now(UTC) - timedelta(days=self._settings.billing_cycle_days)
        current_usage = await self.get_usage(user_id, resource_type, since=period_start)

        return current_usage >= limit, current_usage, limit


# Global instance for convenience
_billing_service: BillingService | None = None


def get_billing_service() -> BillingService:
    """Get or create the global billing service."""
    global _billing_service
    if _billing_service is None:
        _billing_service = BillingService()
    return _billing_service


async def record_usage(
    user_id: str,
    resource_type: str,
    quantity: int = 1,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Convenience function to record usage.

    Args:
        user_id: User identifier
        resource_type: Type of resource used
        quantity: Amount used
        metadata: Additional metadata
    """
    service = get_billing_service()
    await service.record_usage(user_id, resource_type, quantity, metadata)


async def get_billing_summary(
    user_id: str,
    tier: SubscriptionTier,
) -> BillingSummary:
    """Convenience function to get billing summary.

    Args:
        user_id: User identifier
        tier: Subscription tier

    Returns:
        BillingSummary
    """
    service = get_billing_service()
    return await service.get_billing_summary(user_id, tier)
