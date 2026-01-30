"""
Usage metering service.

Tracks API usage and calculates costs based on tier limits.
"""

from __future__ import annotations

import logging

from ...config import get_settings
from ...models.payment import SubscriptionTier
from ...models.subscription import UsageRecord
from ...repositories.usage import UsageRepository

logger = logging.getLogger(__name__)


class UsageMeter:
    """Service for tracking and calculating API usage."""

    # Cost units per endpoint type
    ENDPOINT_COSTS = {
        "relationship_analysis": 1,
        "entity_extraction": 1,
        "batch_analysis": 10,  # Batch operations cost more
        "scenario_analysis": 5,
    }

    def __init__(self, usage_repo: UsageRepository | None = None):
        """
        Initialize usage meter.

        Args:
            usage_repo: Usage repository (created if not provided)
        """
        self.usage_repo = usage_repo or UsageRepository()
        self.settings = get_settings()

    def get_cost_units(self, endpoint: str) -> int:
        """
        Get cost units for an endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            Cost units (1 for most endpoints, higher for expensive operations)
        """
        # Extract endpoint type from path
        endpoint_type = endpoint.split("/")[-1] if "/" in endpoint else endpoint

        # Check for batch operations
        if "batch" in endpoint.lower():
            return self.ENDPOINT_COSTS.get("batch_analysis", 10)

        # Map common endpoints
        if "relationship" in endpoint_type:
            return self.ENDPOINT_COSTS.get("relationship_analysis", 1)
        elif "entity" in endpoint_type or "ner" in endpoint_type:
            return self.ENDPOINT_COSTS.get("entity_extraction", 1)
        elif "scenario" in endpoint_type:
            return self.ENDPOINT_COSTS.get("scenario_analysis", 5)

        return 1  # Default cost

    async def record_usage(
        self,
        user_id: str,
        endpoint: str,
        api_key_id: str | None = None,
        cost_units: int | None = None,
        metadata: dict | None = None,
    ) -> UsageRecord:
        """
        Record API usage.

        Args:
            user_id: User identifier
            endpoint: API endpoint path
            api_key_id: API key ID (if used)
            cost_units: Cost units (calculated if not provided)
            metadata: Additional metadata

        Returns:
            Created usage record
        """
        import uuid

        if cost_units is None:
            cost_units = self.get_cost_units(endpoint)

        record = UsageRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            api_key_id=api_key_id,
            endpoint=endpoint,
            cost_units=cost_units,
            metadata=metadata or {},
        )

        await self.usage_repo.add(record)
        return record

    async def get_tier_limits(self, tier: SubscriptionTier) -> dict[str, int]:
        """
        Get usage limits for a subscription tier.

        Args:
            tier: Subscription tier

        Returns:
            Dictionary of endpoint type to limit
        """
        settings = self.settings.billing

        if tier == SubscriptionTier.FREE:
            return {
                "relationship_analysis": settings.free_tier_relationship_analyses,
                "entity_extraction": settings.free_tier_entity_extractions,
            }
        elif tier == SubscriptionTier.STARTER:
            return {
                "relationship_analysis": settings.starter_tier_relationship_analyses,
                "entity_extraction": settings.starter_tier_entity_extractions,
            }
        elif tier == SubscriptionTier.PROFESSIONAL:
            return {
                "relationship_analysis": settings.pro_tier_relationship_analyses,
                "entity_extraction": settings.pro_tier_entity_extractions,
            }
        else:  # ENTERPRISE
            return {
                "relationship_analysis": 999999999,  # Unlimited
                "entity_extraction": 999999999,
            }

    async def check_usage_limit(
        self, user_id: str, tier: SubscriptionTier, endpoint: str, period_days: int = 30
    ) -> tuple[bool, int, int]:
        """
        Check if user has exceeded usage limit for an endpoint.

        Args:
            user_id: User identifier
            tier: Subscription tier
            endpoint: API endpoint path
            period_days: Billing period in days

        Returns:
            Tuple of (within_limit, current_usage, limit)
        """
        limits = await self.get_tier_limits(tier)

        # Map endpoint to limit type
        if "relationship" in endpoint:
            limit_type = "relationship_analysis"
        elif "entity" in endpoint or "ner" in endpoint:
            limit_type = "entity_extraction"
        else:
            limit_type = "entity_extraction"  # Default

        limit = limits.get(limit_type, 0)
        current_usage = await self.usage_repo.get_usage_by_endpoint(user_id, endpoint, period_days)

        return current_usage < limit, current_usage, limit
