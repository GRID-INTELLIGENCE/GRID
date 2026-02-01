"""
CostTier and Usage Aggregation Module.
Handles tier definitions and periodic usage rollup.
"""

import logging
from datetime import UTC, datetime
from enum import Enum

from src.application.mothership.config import MothershipSettings
from src.grid.infrastructure.database import DatabaseManager

logger = logging.getLogger(__name__)
settings = MothershipSettings.from_env()


class CostTier(str, Enum):
    """Subscription tier definitions."""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# Tier limits configuration (from settings or constants)
TIER_LIMITS = {
    CostTier.FREE: {
        "relationship_analysis": settings.billing.free_tier_relationship_analyses,
        "entity_extraction": settings.billing.free_tier_entity_extractions,
        "resonance_event": settings.billing.free_tier_resonance_events,
        "monthly_price_cents": 0,
    },
    CostTier.STARTER: {
        "relationship_analysis": settings.billing.starter_tier_relationship_analyses,
        "entity_extraction": settings.billing.starter_tier_entity_extractions,
        "resonance_event": settings.billing.starter_tier_resonance_events,
        "monthly_price_cents": settings.billing.starter_monthly_price,
    },
    CostTier.PRO: {
        "relationship_analysis": settings.billing.pro_tier_relationship_analyses,
        "entity_extraction": settings.billing.pro_tier_entity_extractions,
        "resonance_event": settings.billing.pro_tier_resonance_events,
        "monthly_price_cents": settings.billing.pro_monthly_price,
    },
    CostTier.ENTERPRISE: {
        "relationship_analysis": -1,  # Unlimited
        "entity_extraction": -1,
        "resonance_event": -1,
        "monthly_price_cents": 0,  # Custom pricing
    },
}


class UsageAggregator:
    """
    Aggregates raw usage_logs into daily/monthly summaries.
    Should be run periodically (e.g., via scheduled task or after batch flush).
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def aggregate_daily(self, user_id: str, date: str = None) -> None:
        """
        Aggregate usage for a specific day.
        Date format: 'YYYY-MM-DD'. Defaults to today.
        """
        if date is None:
            date = datetime.now(UTC).strftime("%Y-%m-%d")

        # Sum usage_logs for the day
        query = """
        SELECT event_type, SUM(quantity) as total
        FROM usage_logs
        WHERE user_id = ? AND DATE(timestamp) = DATE(?)
        GROUP BY event_type
        """
        rows = await self.db.fetch_all(query, (user_id, date))

        for row in rows:
            # Upsert into usage_aggregation
            upsert = """
            INSERT INTO usage_aggregation (user_id, period, period_type, event_type, total_quantity, updated_at)
            VALUES (?, ?, 'daily', ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, period, period_type, event_type)
            DO UPDATE SET total_quantity = excluded.total_quantity, updated_at = CURRENT_TIMESTAMP
            """
            await self.db.execute(upsert, (user_id, date, row["event_type"], row["total"]))

        await self.db.commit()
        logger.debug(f"Aggregated daily usage for {user_id} on {date}")

    async def aggregate_monthly(self, user_id: str, month: str = None) -> None:
        """
        Aggregate usage for a specific month.
        Month format: 'YYYY-MM'. Defaults to current month.
        """
        if month is None:
            month = datetime.now(UTC).strftime("%Y-%m")

        # Sum usage_logs for the month
        query = """
        SELECT event_type, SUM(quantity) as total
        FROM usage_logs
        WHERE user_id = ? AND strftime('%Y-%m', timestamp) = ?
        GROUP BY event_type
        """
        rows = await self.db.fetch_all(query, (user_id, month))

        for row in rows:
            upsert = """
            INSERT INTO usage_aggregation (user_id, period, period_type, event_type, total_quantity, updated_at)
            VALUES (?, ?, 'monthly', ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, period, period_type, event_type)
            DO UPDATE SET total_quantity = excluded.total_quantity, updated_at = CURRENT_TIMESTAMP
            """
            await self.db.execute(upsert, (user_id, month, row["event_type"], row["total"]))

        await self.db.commit()
        logger.debug(f"Aggregated monthly usage for {user_id} for {month}")

    async def get_monthly_aggregation(self, user_id: str, month: str = None) -> dict[str, int]:
        """Get aggregated usage for a month."""
        if month is None:
            month = datetime.now(UTC).strftime("%Y-%m")

        query = """
        SELECT event_type, total_quantity
        FROM usage_aggregation
        WHERE user_id = ? AND period = ? AND period_type = 'monthly'
        """
        rows = await self.db.fetch_all(query, (user_id, month))
        return {r["event_type"]: r["total_quantity"] for r in rows}
