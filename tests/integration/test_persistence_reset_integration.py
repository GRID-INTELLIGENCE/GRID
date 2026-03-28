"""
Persistence Reset Integration Tests for GRID Admission Gate

Tests reset-aware persistence with file-backed SQLite database.
Verifies that full_reset operations are properly persisted and loaded.
"""

import tempfile
import time
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from application.mothership.db.models_base import Base
from application.mothership.db.models_admission import AdmissionEntityRow, AdmissionViolationRow
from application.mothership.middleware.admission_gate import EntityAttributionEngine, EntityRecord, ViolationType
from application.mothership.repositories.admission import AdmissionEntityRepository


class TestPersistenceResetIntegration:
    """Test persistence reset behavior with file-backed SQLite."""

    @pytest.fixture
    async def temp_db_engine(self):
        """Create temporary file-backed SQLite database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            db_path = temp_file.name

        # Create async engine with file-backed SQLite
        engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield engine, db_path

        # Cleanup
        await engine.dispose()
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    async def repository(self, temp_db_engine):
        """Create repository with temp database."""
        engine, db_path = temp_db_engine
        session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        return AdmissionEntityRepository(session_factory), db_path

    async def test_full_reset_persistence_cycle(self, repository):
        """Test complete cycle: persist → full_reset → persist → load → verify."""
        repo, db_path = repository

        # Create attribution engine and add violations
        engine = EntityAttributionEngine()
        entity_id = "test-entity-reset"

        # Add 3 violations
        engine.record_violation(entity_id, ViolationType.BUDGET_EXCEEDED)
        engine.record_violation(entity_id, ViolationType.CONTEXT_OVERFLOW)
        engine.record_violation(entity_id, ViolationType.ORIGIN_DENIED)

        # Persist initial state
        record = engine.get_record(entity_id)
        await repo.persist_entity(record)

        # Verify initial persistence
        loaded_entities = await repo.load_all()
        assert entity_id in loaded_entities
        loaded_record = loaded_entities[entity_id]
        assert len(loaded_record.violations) == 3
        assert loaded_record.total_penalty_points == 23  # Each violation has different penalty points
        assert not loaded_record.bannered

        # Perform full reset
        engine.reset()

        # Verify in-memory reset
        reset_record = engine.get_record(entity_id)
        assert len(reset_record.violations) == 0
        assert reset_record.total_penalty_points == 0
        assert not reset_record.bannered

        # Persist reset state
        await repo.persist_entity(reset_record)

        # Load and verify reset persistence
        final_entities = await repo.load_all()
        final_record = final_entities[entity_id]
        assert len(final_record.violations) == 0
        assert final_record.total_penalty_points == 0
        assert not final_record.bannered

    async def test_partial_reset_scenario(self, repository):
        """Test edge case: partial reset (some violations cleared but not all)."""
        repo, db_path = repository

        # Create attribution engine and add violations
        engine = EntityAttributionEngine()
        entity_id = "test-entity-partial"

        # Add 5 violations
        for i in range(5):
            engine.record_violation(entity_id, ViolationType.BUDGET_EXCEEDED)

        # Persist initial state
        record = engine.get_record(entity_id)
        await repo.persist_entity(record)

        # Simulate partial reset by manually creating a record with fewer violations
        # This could happen if some violations were manually cleared
        partial_record = EntityRecord(
            entity_id=entity_id,
            violations=record.violations[:2],  # Keep only first 2 violations
            total_penalty_points=2,
            bannered=False,
            banner_reason="",
            first_seen=time.monotonic(),
            last_seen=time.monotonic(),
        )

        # Persist partial state
        await repo.persist_entity(partial_record)

        # Load and verify partial reset was handled correctly
        loaded_entities = await repo.load_all()
        loaded_record = loaded_entities[entity_id]
        assert len(loaded_record.violations) == 2
        assert loaded_record.total_penalty_points == 2

    async def test_bannered_entity_reset(self, repository):
        """Test reset of bannered entities (unbanner scenario)."""
        repo, db_path = repository

        # Create attribution engine and banner an entity
        engine = EntityAttributionEngine()
        entity_id = "test-entity-bannered"

        # Add enough violations to trigger automatic banner
        for i in range(20):  # This should trigger banner at threshold
            engine.record_violation(entity_id, ViolationType.BUDGET_EXCEEDED)

        # Get the record (should be bannered automatically)
        record = engine.get_record(entity_id)

        # Persist bannered state
        await repo.persist_entity(record)

        # Verify bannered persistence
        loaded_entities = await repo.load_all()
        loaded_record = loaded_entities[entity_id]
        assert loaded_record.bannered
        assert "penalty_threshold_exceeded" in loaded_record.banner_reason
        assert loaded_record.total_penalty_points >= 50

        # Perform reset (should unbanner)
        engine.reset()
        reset_record = engine.get_record(entity_id)
        await repo.persist_entity(reset_record)

        # Verify unbanner persistence
        final_entities = await repo.load_all()
        final_record = final_entities[entity_id]
        assert not final_record.bannered
        assert final_record.banner_reason == ""
        assert final_record.total_penalty_points == 0

    async def test_multiple_entities_reset(self, repository):
        """Test reset with multiple entities simultaneously."""
        repo, db_path = repository

        # Create attribution engine with multiple entities
        engine = EntityAttributionEngine()
        entities = ["entity-1", "entity-2", "entity-3"]

        # Add violations to each entity
        for entity_id in entities:
            for i in range(3):
                engine.record_violation(entity_id, ViolationType.BUDGET_EXCEEDED)

        # Persist all entities
        for entity_id in entities:
            record = engine.get_record(entity_id)
            await repo.persist_entity(record)

        # Verify initial state
        loaded_entities = await repo.load_all()
        assert len(loaded_entities) == 3
        for entity_id in entities:
            assert len(loaded_entities[entity_id].violations) == 3

        # Full reset
        engine.reset()

        # Persist reset for all entities
        for entity_id in entities:
            reset_record = engine.get_record(entity_id)
            await repo.persist_entity(reset_record)

        # Verify all entities reset
        final_entities = await repo.load_all()
        assert len(final_entities) == 3
        for entity_id in entities:
            final_record = final_entities[entity_id]
            assert len(final_record.violations) == 0
            assert final_record.total_penalty_points == 0
            assert not final_record.bannered

    async def test_violation_metadata_persistence(self, repository):
        """Test that violation metadata survives reset cycles."""
        repo, db_path = repository

        # Create attribution engine
        engine = EntityAttributionEngine()
        entity_id = "test-entity-metadata"

        # Add violation with metadata
        metadata = {"request_path": "/api/v1/test", "user_agent": "test-agent"}
        engine.record_violation(
            entity_id,
            ViolationType.CONTEXT_OVERFLOW,
            metadata=metadata
        )

        # Persist
        record = engine.get_record(entity_id)
        await repo.persist_entity(record)

        # Verify metadata persistence
        loaded_entities = await repo.load_all()
        loaded_record = loaded_entities[entity_id]
        assert len(loaded_record.violations) == 1
        assert loaded_record.violations[0].metadata == metadata

        # Reset and persist
        engine.reset()
        reset_record = engine.get_record(entity_id)
        await repo.persist_entity(reset_record)

        # Verify reset (no violations, no metadata)
        final_entities = await repo.load_all()
        final_record = final_entities[entity_id]
        assert len(final_record.violations) == 0
