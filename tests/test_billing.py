"""Test script for billing service."""

import sys

sys.path.insert(0, "src")

import pytest

from src.grid.billing import BillingService, CostTier
from src.grid.infrastructure.database import DatabaseManager


@pytest.fixture
async def billing_setup(tmp_path):
    db_path = str(tmp_path / "billing_test.db")
    db = DatabaseManager(db_path)
    await db.initialize_schema()
    billing = BillingService(db)
    yield billing, db
    await db.close()


@pytest.mark.asyncio
async def test_billing_tier_management(billing_setup):
    billing, db = billing_setup
    user_id = "user_123"

    # Default tier should be FREE
    tier = await billing.get_user_tier(user_id)
    assert tier == CostTier.FREE

    # Set to STARTER
    await billing.set_user_tier(user_id, CostTier.STARTER)
    tier = await billing.get_user_tier(user_id)
    assert tier == CostTier.STARTER


@pytest.mark.asyncio
async def test_billing_usage_summary(billing_setup):
    billing, db = billing_setup
    user_id = "user_456"

    await billing.set_user_tier(user_id, CostTier.STARTER)
    summary = await billing.get_usage_summary(user_id)

    assert summary["tier"] == "starter"
    assert "current_bill_cents" in summary
