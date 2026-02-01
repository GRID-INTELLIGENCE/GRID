"""
Billing Service - Cost Calculation and Plan Management.
"""

import logging

from src.application.mothership.config import MothershipSettings
from src.grid.billing.aggregation import TIER_LIMITS, CostTier, UsageAggregator
from src.grid.infrastructure.database import DatabaseManager

logger = logging.getLogger(__name__)
settings = MothershipSettings.from_env()


class BillingService:
    """
    Domain service for Billing logic: Cost Calculation, Plan Limits, Tier Management.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.aggregator = UsageAggregator(db_manager)

    async def get_user_tier(self, user_id: str) -> CostTier:
        """Get user's current subscription tier."""
        row = await self.db.fetch_one("SELECT tier FROM subscriptions WHERE user_id = ?", (user_id,))
        if row:
            try:
                return CostTier(row["tier"])
            except ValueError:
                return CostTier.FREE
        return CostTier.FREE

    async def set_user_tier(self, user_id: str, tier: CostTier, stripe_sub_id: str = None) -> None:
        """Set or update user's subscription tier."""
        import uuid

        existing = await self.db.fetch_one("SELECT id FROM subscriptions WHERE user_id = ?", (user_id,))
        if existing:
            await self.db.execute(
                "UPDATE subscriptions SET tier = ?, stripe_subscription_id = ? WHERE user_id = ?",
                (tier.value, stripe_sub_id, user_id),
            )
        else:
            await self.db.execute(
                "INSERT INTO subscriptions (id, user_id, tier, stripe_subscription_id) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), user_id, tier.value, stripe_sub_id),
            )
        await self.db.commit()

    async def get_total_usage(self, user_id: str, month: str = None) -> dict[str, int]:
        """Get aggregated usage for a user (from aggregation table if available)."""
        usage = await self.aggregator.get_monthly_aggregation(user_id, month)
        if usage:
            return usage

        # Fallback to raw query if aggregation not yet run
        query = """
        SELECT event_type, SUM(quantity) as total
        FROM usage_logs
        WHERE user_id = ?
        GROUP BY event_type
        """
        rows = await self.db.fetch_all(query, (user_id,))
        return {r["event_type"]: r["total"] for r in rows}

    async def calculate_current_bill(self, user_id: str) -> int:
        """Calculate current bill in cents based on usage and tier overages."""
        usage = await self.get_total_usage(user_id)
        tier = await self.get_user_tier(user_id)
        limits = TIER_LIMITS.get(tier, TIER_LIMITS[CostTier.FREE])

        # Base price
        total_cents = limits.get("monthly_price_cents", 0)

        # Calculate overages
        for event_type, limit in limits.items():
            if event_type == "monthly_price_cents":
                continue
            if limit == -1:  # Unlimited
                continue

            used = usage.get(event_type, 0)
            if used > limit:
                overage = used - limit
                # Get overage rate from settings
                overage_rate = getattr(settings.billing, f"{event_type}_overage_cents", 1)  # Default 1 cent per unit
                total_cents += overage * overage_rate

        return total_cents

    async def check_resource_access(self, user_id: str, resource_type: str) -> bool:
        """
        Check if user is allowed to access resource (within hard limits).
        Returns False if user has exceeded their tier limit.
        """
        tier = await self.get_user_tier(user_id)
        limits = TIER_LIMITS.get(tier, TIER_LIMITS[CostTier.FREE])
        limit = limits.get(resource_type, 0)

        if limit == -1:  # Unlimited
            return True

        usage = await self.get_total_usage(user_id)
        used = usage.get(resource_type, 0)

        return used < limit

    async def get_usage_summary(self, user_id: str) -> dict:
        """Get comprehensive usage summary with limits and overages."""
        tier = await self.get_user_tier(user_id)
        usage = await self.get_total_usage(user_id)
        limits = TIER_LIMITS.get(tier, TIER_LIMITS[CostTier.FREE])
        bill = await self.calculate_current_bill(user_id)

        summary = {
            "tier": tier.value,
            "monthly_price_cents": limits.get("monthly_price_cents", 0),
            "current_bill_cents": bill,
            "usage": {},
        }

        for event_type, limit in limits.items():
            if event_type == "monthly_price_cents":
                continue
            used = usage.get(event_type, 0)
            summary["usage"][event_type] = {
                "used": used,
                "limit": limit if limit != -1 else "unlimited",
                "overage": max(0, used - limit) if limit != -1 else 0,
            }

        return summary
