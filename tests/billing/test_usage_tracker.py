import asyncio

import pytest

from src.grid.billing.usage_tracker import UsageTracker
from src.grid.infrastructure.database import DatabaseManager


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_grid.db")


@pytest.fixture
async def db_manager(db_path):
    db = DatabaseManager(db_path)
    await db.initialize_schema()  # Creates usage_logs table
    yield db
    await db.close()


@pytest.fixture
async def usage_tracker(db_manager):
    # Small batch size for easy flushing testing
    tracker = UsageTracker(db_manager, batch_size=2, flush_interval=10)
    await tracker.start()
    yield tracker
    await tracker.stop()


@pytest.mark.asyncio
async def test_track_event_buffering(usage_tracker, db_manager):
    # Track 1 event (buffer size < 2)
    await usage_tracker.track_event("u1", "api_call", 1)

    # Check DB - should be empty (not flushed yet)
    logs = await db_manager.fetch_all("SELECT * FROM usage_logs")
    assert len(logs) == 0

    # Track 2nd event -> flush triggered
    await usage_tracker.track_event("u1", "api_call", 1)

    # Pause to let async flush happen
    await asyncio.sleep(0.1)

    logs = await db_manager.fetch_all("SELECT * FROM usage_logs")
    assert len(logs) == 2
    assert logs[0]["user_id"] == "u1"


@pytest.mark.asyncio
async def test_manual_flush(usage_tracker, db_manager):
    await usage_tracker.track_event("u2", "gpu_usage", 5)
    await usage_tracker.flush()

    logs = await db_manager.fetch_all("SELECT * FROM usage_logs WHERE user_id='u2'")
    assert len(logs) == 1
    assert logs[0]["quantity"] == 5
