import asyncio

import pytest
import pytest_asyncio

from src.grid.billing.usage_tracker import UsageTracker
from src.grid.infrastructure.database import DatabaseManager


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_grid.db")


@pytest_asyncio.fixture
async def db_manager(db_path):
    db = DatabaseManager(db_path)
    await db.initialize_schema()  # Creates usage_logs table
    yield db
    await db.close()


@pytest_asyncio.fixture
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


@pytest.mark.asyncio
async def test_burst_enqueue_no_task_fanout(db_manager):
    """Burst: many concurrent track_event calls must not create flush task fan-out."""
    tracker = UsageTracker(db_manager, batch_size=50, flush_interval=10)
    await tracker.start()

    # Enqueue 200 events concurrently
    await asyncio.gather(*[tracker.track_event("burst", "api_call") for _ in range(200)])

    # Give worker a moment to process batches
    await asyncio.sleep(0.2)
    await tracker.stop()

    logs = await db_manager.fetch_all("SELECT * FROM usage_logs WHERE user_id='burst'")
    assert len(logs) == 200
    assert tracker.events_enqueued == 200
    assert tracker.events_flushed == 200
    assert tracker.events_dropped == 0


@pytest.mark.asyncio
async def test_queue_full_routes_to_dead_letter(db_manager):
    """Queue-full events go to dead-letter; dropped counter increments."""
    tracker = UsageTracker(db_manager, batch_size=100, flush_interval=10, max_queue_size=2)
    await tracker.start()

    # Overload the tiny queue without giving the worker time to drain
    for _ in range(5):
        await tracker.track_event("overflow", "api_call")

    assert tracker.events_dropped > 0
    assert len(tracker._dead_letter) > 0

    await tracker.stop()


@pytest.mark.asyncio
async def test_flush_retry_on_db_failure(db_manager):
    """On DB write failure, events go to dead-letter and are retried."""
    from unittest.mock import AsyncMock, patch

    tracker = UsageTracker(db_manager, batch_size=100, flush_interval=10)
    await tracker.start()

    await tracker.track_event("retry_user", "api_call")

    fail_count = 0

    async def flaky_execute_many(query, params):
        nonlocal fail_count
        if fail_count < 1:
            fail_count += 1
            raise RuntimeError("DB write error")
        return await db_manager.__class__.execute_many(db_manager, query, params)

    with patch.object(db_manager, "execute_many", side_effect=flaky_execute_many):
        await tracker.flush()  # First attempt fails → dead-letter

    assert len(tracker._dead_letter) == 1
    assert tracker.flush_failures == 1

    # Second flush: dead-letter retried successfully
    await tracker.flush()
    logs = await db_manager.fetch_all("SELECT * FROM usage_logs WHERE user_id='retry_user'")
    assert len(logs) == 1

    await tracker.stop()


@pytest.mark.asyncio
async def test_graceful_shutdown_drains_queue(db_manager):
    """stop() ensures all enqueued events are persisted before exit."""
    tracker = UsageTracker(db_manager, batch_size=100, flush_interval=30)
    await tracker.start()

    for i in range(10):
        await tracker.track_event(f"shutdown_{i}", "api_call")

    await tracker.stop()  # Must drain and persist all 10

    logs = await db_manager.fetch_all("SELECT * FROM usage_logs")
    assert len(logs) == 10
    assert tracker.events_flushed == 10
