"""Tests for admission gate entity persistence via SQLite."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from application.mothership.db.models_base import Base
from application.mothership.middleware.admission_gate import (
    EntityAttributionEngine,
    EntityRecord,
    ViolationType,
)
from application.mothership.repositories.admission import AdmissionEntityRepository


@pytest.fixture
async def session_factory():
    """Create an in-memory SQLite engine + session factory for testing."""
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


class TestAdmissionPersistence:
    """Tests for AdmissionEntityRepository CRUD operations."""

    async def test_persist_and_load_entity(self, repo: AdmissionEntityRepository) -> None:
        engine = EntityAttributionEngine(banner_threshold=50)
        engine.record_violation("entity-1", ViolationType.BUDGET_EXCEEDED)
        engine.record_violation("entity-1", ViolationType.ORIGIN_DENIED)

        record = engine.get_record("entity-1")
        await repo.persist_entity(record)

        loaded = await repo.load_all()
        assert "entity-1" in loaded
        assert loaded["entity-1"].violation_count == 2
        assert loaded["entity-1"].total_penalty_points == record.total_penalty_points

    async def test_persist_bannered_entity(self, repo: AdmissionEntityRepository) -> None:
        engine = EntityAttributionEngine(banner_threshold=10)
        engine.record_violation("bad-actor", ViolationType.PROFIT_MASKING, profit_masked=True)

        record = engine.get_record("bad-actor")
        assert record.bannered is True

        await repo.persist_entity(record)

        loaded = await repo.load_all()
        assert loaded["bad-actor"].bannered is True
        assert loaded["bad-actor"].total_penalty_points >= 10

    async def test_persist_updates_existing(self, repo: AdmissionEntityRepository) -> None:
        engine = EntityAttributionEngine(banner_threshold=100)
        engine.record_violation("entity-2", ViolationType.BUDGET_EXCEEDED)
        await repo.persist_entity(engine.get_record("entity-2"))

        # Add more violations
        engine.record_violation("entity-2", ViolationType.CONTEXT_OVERFLOW)
        await repo.persist_entity(engine.get_record("entity-2"))

        loaded = await repo.load_all()
        assert loaded["entity-2"].violation_count == 2

    async def test_delete_entity(self, repo: AdmissionEntityRepository) -> None:
        engine = EntityAttributionEngine(banner_threshold=100)
        engine.record_violation("doomed", ViolationType.BUDGET_EXCEEDED)
        await repo.persist_entity(engine.get_record("doomed"))

        await repo.delete_entity("doomed")

        loaded = await repo.load_all()
        assert "doomed" not in loaded

    async def test_load_empty_returns_empty_dict(self, repo: AdmissionEntityRepository) -> None:
        loaded = await repo.load_all()
        assert loaded == {}

    async def test_ensure_tables_idempotent(self, repo: AdmissionEntityRepository) -> None:
        await repo.ensure_tables()
        await repo.ensure_tables()  # Should not raise
