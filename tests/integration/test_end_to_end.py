import asyncio

import pytest

from src.grid.auth.service import AuthService
from src.grid.auth.token_manager import TokenManager
from src.grid.billing.aggregation import CostTier
from src.grid.billing.service import BillingService
from src.grid.billing.usage_tracker import UsageTracker
from src.grid.infrastructure.database import DatabaseManager


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "e2e_grid.db")


@pytest.fixture(autouse=True)
def auth_env(monkeypatch):
    monkeypatch.setenv("MOTHERSHIP_SECRET_KEY", "test-secret-key-123")
    monkeypatch.setenv("MOTHERSHIP_JWT_ALGORITHM", "HS256")


@pytest.fixture
async def services(db_path):
    # Setup Infrastructure
    db = DatabaseManager(db_path)
    await db.initialize_schema()

    # Setup Auth
    tm = TokenManager()
    auth = AuthService(db, tm)

    # Setup Usage & Billing
    tracker = UsageTracker(db, batch_size=1, flush_interval=0.1)  # Flush fast
    await tracker.start()

    billing = BillingService(db)

    yield {"db": db, "auth": auth, "tracker": tracker, "billing": billing}

    await tracker.stop()
    await db.close()


@pytest.mark.asyncio
async def test_end_to_end_flow(services):
    auth = services["auth"]
    tracker = services["tracker"]
    billing = services["billing"]

    # 1. Register
    user_id = await auth.register_user("e2e_user", "secure_password")
    assert user_id is not None

    # 2. Login
    tokens = await auth.login("e2e_user", "secure_password")
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # 3. Track Usage (Relationship Analysis)
    # Using 'relationship_analysis' event type
    await tracker.track_event(user_id, "relationship_analysis", 500)

    # Wait for flush
    await asyncio.sleep(0.5)

    # 4. Set tier to STARTER and check bill
    await billing.set_user_tier(user_id, CostTier.STARTER)

    # 500 < 1000 limit, so no overage. Base = $49.00
    bill = await billing.calculate_current_bill(user_id)
    assert bill == 4900  # $49.00

    # 5. Create Overage
    await tracker.track_event(user_id, "relationship_analysis", 600)  # Total 1100
    await asyncio.sleep(0.5)

    # Limit is 1000. Overage 100. Cost 5 cents each = 500 cents.
    # Total = 4900 + 500 = 5400
    bill_overage = await billing.calculate_current_bill(user_id)
    assert bill_overage == 5400


@pytest.mark.asyncio
async def test_auth_refresh_flow(services):
    auth = services["auth"]

    # Register & Login
    await auth.register_user("refresh_user", "password")
    tokens = await auth.login("refresh_user", "password")
    refresh_token = tokens["refresh_token"]

    # Refresh
    new_tokens = await auth.refresh_access(refresh_token)
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != refresh_token

    # Old refresh token should be revoked
    with pytest.raises(ValueError, match="Invalid refresh token"):
        await auth.refresh_access(refresh_token)
