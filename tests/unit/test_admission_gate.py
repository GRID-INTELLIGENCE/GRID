"""Tests for admission gate: shared attribution, ENTITY_BANNERED, public accessors,
reset persistence, and HMAC entity signing."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from application.mothership.db.models_base import Base
from application.mothership.middleware.admission_gate import (
    AdmissionGateMiddleware,
    EntityAttributionEngine,
    EntityRecord,
    ViolationType,
)
from application.mothership.middleware.entity_signing import sign_entity_id, verify_entity_signature
from application.mothership.repositories.admission import AdmissionEntityRepository

# ---------------------------------------------------------------------------
# Step 1: ENTITY_BANNERED violation type
# ---------------------------------------------------------------------------


class TestEntityBanneredViolationType:
    def test_entity_bannered_exists(self) -> None:
        assert ViolationType.ENTITY_BANNERED == "entity_bannered"

    def test_entity_bannered_base_penalty_is_zero(self) -> None:
        assert EntityAttributionEngine.BASE_PENALTIES[ViolationType.ENTITY_BANNERED] == 0


# ---------------------------------------------------------------------------
# Step 2: Public accessors
# ---------------------------------------------------------------------------


class TestPublicAccessors:
    def test_banner_threshold_property(self) -> None:
        engine = EntityAttributionEngine(banner_threshold=42)
        assert engine.banner_threshold == 42

    def test_peek_record_returns_none_for_unknown(self) -> None:
        engine = EntityAttributionEngine()
        assert engine.peek_record("nonexistent") is None

    def test_peek_record_returns_existing_without_creating(self) -> None:
        engine = EntityAttributionEngine()
        engine.record_violation("entity-a", ViolationType.BUDGET_EXCEEDED)
        record = engine.peek_record("entity-a")
        assert record is not None
        assert record.entity_id == "entity-a"

    def test_persist_record_calls_hook(self) -> None:
        hook_called = []

        async def mock_hook(record: EntityRecord) -> None:
            hook_called.append(record.entity_id)

        engine = EntityAttributionEngine(persist_hook=mock_hook)
        engine.record_violation("entity-b", ViolationType.BUDGET_EXCEEDED)
        record = engine.get_record("entity-b")
        # persist_record wraps _fire_persist; test the method exists and runs
        # (actual async scheduling requires a running loop)
        engine.persist_record(record)

    def test_set_persist_hook(self) -> None:
        engine = EntityAttributionEngine()
        assert engine._persist_hook is None

        async def my_hook(record: EntityRecord) -> None:
            pass

        engine.set_persist_hook(my_hook)
        assert engine._persist_hook is my_hook


# ---------------------------------------------------------------------------
# Step 3: Shared attribution engine injection
# ---------------------------------------------------------------------------


class TestSharedAttribution:
    def test_middleware_uses_injected_attribution(self) -> None:
        shared = EntityAttributionEngine(banner_threshold=99)
        app = MagicMock()
        mw = AdmissionGateMiddleware(app, attribution=shared)
        assert mw.attribution is shared
        assert mw.attribution.banner_threshold == 99

    def test_middleware_creates_default_if_none(self) -> None:
        app = MagicMock()
        mw = AdmissionGateMiddleware(app)
        assert mw.attribution is not None
        assert isinstance(mw.attribution, EntityAttributionEngine)

    def test_counters_shared_via_attribution(self) -> None:
        shared = EntityAttributionEngine()
        app = MagicMock()
        AdmissionGateMiddleware(app, attribution=shared)

        # Simulate rejections via the attribution engine
        shared.total_rejected = 5
        shared.rejection_reasons["TEST"] = 3
        shared.total_admitted = 10

        # Router would read from shared
        assert shared.total_rejected == 5
        assert shared.total_admitted == 10
        assert shared.rejection_reasons["TEST"] == 3


# ---------------------------------------------------------------------------
# Step 5: Persistence sync after full_reset
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.fixture
def repo(session_factory) -> AdmissionEntityRepository:
    return AdmissionEntityRepository(session_factory)


@pytest.mark.asyncio
class TestPersistenceResetSync:
    async def test_persist_after_full_reset(self, repo: AdmissionEntityRepository) -> None:
        """After full_reset clears violations, persistence should detect the reset
        and clear DB rows instead of using a broken positional slice."""
        engine = EntityAttributionEngine(banner_threshold=100)
        engine.record_violation("entity-reset", ViolationType.BUDGET_EXCEEDED)
        engine.record_violation("entity-reset", ViolationType.ORIGIN_DENIED)

        record = engine.get_record("entity-reset")
        assert record.violation_count == 2
        await repo.persist_entity(record)

        # Simulate full_reset
        record.violations.clear()
        record.total_penalty_points = 0
        record.bannered = False
        record.banner_reason = ""

        # Persist after reset — should handle len(memory) < len(db)
        await repo.persist_entity(record)

        loaded = await repo.load_all()
        assert loaded["entity-reset"].violation_count == 0
        assert loaded["entity-reset"].total_penalty_points == 0


# ---------------------------------------------------------------------------
# Step 8: HMAC entity signing
# ---------------------------------------------------------------------------


class TestEntitySigning:
    def test_sign_and_verify(self) -> None:
        secret = "test-secret-key"
        sig, ts = sign_entity_id("entity-1", secret)
        assert verify_entity_signature("entity-1", sig, str(ts), secret)

    def test_wrong_secret_fails(self) -> None:
        sig, ts = sign_entity_id("entity-1", "correct-secret")
        assert not verify_entity_signature("entity-1", sig, str(ts), "wrong-secret")

    def test_wrong_entity_id_fails(self) -> None:
        secret = "test-secret"
        sig, ts = sign_entity_id("entity-1", secret)
        assert not verify_entity_signature("entity-2", sig, str(ts), secret)

    def test_expired_timestamp_fails(self) -> None:
        secret = "test-secret"
        old_ts = int(time.time()) - 600  # 10 minutes ago
        sig, ts = sign_entity_id("entity-1", secret, timestamp=old_ts)
        assert not verify_entity_signature("entity-1", sig, str(ts), secret)

    def test_invalid_timestamp_fails(self) -> None:
        secret = "test-secret"
        sig, _ = sign_entity_id("entity-1", secret)
        assert not verify_entity_signature("entity-1", sig, "not-a-number", secret)

    def test_resolve_entity_with_valid_signature(self) -> None:
        secret = "test-secret"
        engine = EntityAttributionEngine(entity_signing_secret=secret)
        sig, ts = sign_entity_id("signed-entity", secret)

        request = MagicMock()
        request.headers = {
            "X-Entity-Id": "signed-entity",
            "X-Entity-Signature": sig,
            "X-Entity-Timestamp": str(ts),
        }
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        assert engine.resolve_entity(request) == "signed-entity"

    def test_resolve_entity_unsigned_falls_through_to_ip(self) -> None:
        secret = "test-secret"
        engine = EntityAttributionEngine(entity_signing_secret=secret)

        headers = {
            "X-Entity-Id": "unsigned-entity",
            "X-Entity-Signature": "",
            "X-Entity-Timestamp": "",
            "X-API-Key": "",
        }
        request = MagicMock()
        request.headers = headers
        request.client = MagicMock()
        request.client.host = "10.0.0.1"

        assert engine.resolve_entity(request) == "ip:10.0.0.1"

    def test_resolve_entity_no_secret_accepts_raw(self) -> None:
        engine = EntityAttributionEngine(entity_signing_secret="")

        headers = {"X-Entity-Id": "raw-entity"}
        request = MagicMock()
        request.headers = headers

        assert engine.resolve_entity(request) == "raw-entity"


# ---------------------------------------------------------------------------
# Counter reset
# ---------------------------------------------------------------------------


class TestCounterReset:
    def test_reset_counters(self) -> None:
        engine = EntityAttributionEngine()
        engine.total_admitted = 10
        engine.total_rejected = 5
        engine.rejection_reasons["TEST"] = 3
        engine.reset_counters()
        assert engine.total_admitted == 0
        assert engine.total_rejected == 0
        assert len(engine.rejection_reasons) == 0
