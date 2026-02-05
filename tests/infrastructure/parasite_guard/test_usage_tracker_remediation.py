import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src")))

from grid.billing.usage_tracker import UsageTracker


@pytest.mark.asyncio
async def test_usage_tracker_flush_recovery():
    """Test that failed flushes move events to dead-letter queue and don't lose them."""
    # Mock DB manager
    db = MagicMock()
    db.execute_many = AsyncMock(side_effect=[Exception("DB Error"), None])  # Fail first, succeed second
    db.commit = AsyncMock()

    tracker = UsageTracker(db, batch_size=2)

    # Track some events
    await tracker.track_event("user1", "query", 1)
    await tracker.track_event("user2", "query", 1)

    # 1. Flush (should fail)
    await tracker.flush()

    # Verify they are in dead-letter
    assert len(tracker._dead_letter) == 2
    assert len(tracker._buffer) == 0

    # 2. Track more events
    await tracker.track_event("user3", "query", 1)

    # 3. Flush again (should succeed and include dead-letter)
    await tracker.flush()

    # Verify execute_many called with all 3 events
    assert db.execute_many.call_count == 2
    # Second call should have [user1, user2, user3]
    args, kwargs = db.execute_many.call_args
    params = args[1]
    assert len(params) == 3

    # Verify queues are empty now
    assert len(tracker._dead_letter) == 0
    assert len(tracker._buffer) == 0


@pytest.mark.asyncio
async def test_usage_tracker_dead_letter_limit():
    """Test that dead-letter queue doesn't grow infinitely."""
    db = MagicMock()
    db.execute_many = AsyncMock(side_effect=Exception("DB Unreachable"))

    tracker = UsageTracker(db, batch_size=1)
    tracker._max_dead_letter_size = 5

    for i in range(10):
        await tracker.track_event(f"user{i}", "event", 1)
        await tracker.flush()

    assert len(tracker._dead_letter) == 5
    # Should keep the newest ones (user5 to user9) or similar
    assert tracker._dead_letter[-1]["user_id"] == "user9"
