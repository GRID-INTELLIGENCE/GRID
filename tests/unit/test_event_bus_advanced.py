"""
Advanced EventBus tests: ordering, persistence/replay, handler isolation, and Redis fallback.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from grid.agentic.event_bus import EventBus


@pytest.fixture()
def event_bus():
    """Create EventBus with in-memory queue (no Redis)."""
    return EventBus(use_redis=False)


@pytest.mark.asyncio
async def test_event_ordering_preserved(event_bus):
    """Published events should be stored in order for history/replay."""
    events = [
        {"event_type": "case.created", "seq": 1},
        {"event_type": "case.categorized", "seq": 2},
        {"event_type": "case.executed", "seq": 3},
    ]

    for evt in events:
        await event_bus.publish(evt)

    history = await event_bus.get_event_history()
    seqs = [e.get("seq") for e in history]
    assert seqs == [1, 2, 3], f"History ordering lost: {seqs}"


@pytest.mark.asyncio
async def test_replay_preserves_order(event_bus):
    """Replaying events should deliver them in original order."""
    delivered: list[int] = []

    async def handler(evt):
        delivered.append(evt.get("seq"))

    await event_bus.subscribe("case.created", handler)

    for i in range(3):
        await event_bus.publish({"event_type": "case.created", "seq": i})

    # Clear deliveries and replay
    delivered.clear()
    await event_bus.replay_events(event_type="case.created")

    assert delivered == [0, 1, 2], f"Replay ordering incorrect: {delivered}"


@pytest.mark.asyncio
async def test_handler_error_isolation(event_bus):
    """One handler failure should not block other handlers."""
    calls: list[str] = []

    async def bad_handler(_):
        calls.append("bad")
        raise RuntimeError("boom")

    async def good_handler(_):
        calls.append("good")

    await event_bus.subscribe("case.created", bad_handler)
    await event_bus.subscribe("case.created", good_handler)

    await event_bus.publish({"event_type": "case.created"})

    # Both handlers should have run despite one failing
    assert "bad" in calls and "good" in calls


@pytest.mark.asyncio
async def test_redis_publish_fallback_to_queue(monkeypatch):
    """When Redis publish fails, EventBus should fall back to in-memory queue."""
    # Enable redis mode but force publish exception
    bus = EventBus(use_redis=True)
    fake_client = MagicMock()
    fake_client.publish = AsyncMock(side_effect=Exception("redis down"))

    bus.redis_client = fake_client
    bus.redis_pubsub = MagicMock()

    received: list[dict] = []

    async def handler(evt):
        received.append(evt)

    await bus.subscribe("case.created", handler)

    await bus.publish({"event_type": "case.created", "payload": 123})

    # Fallback should enqueue and trigger handler
    assert received, "Handler not invoked after Redis failure fallback"
    assert received[0]["payload"] == 123


@pytest.mark.asyncio
async def test_history_limit():
    """History should respect deque maxlen (max_history)."""
    small_bus = EventBus(use_redis=False, max_history=3)
    for i in range(5):
        await small_bus.publish({"event_type": "case.created", "seq": i})

    history = await small_bus.get_event_history()
    seqs = [e.get("seq") for e in history]
    assert seqs == [2, 3, 4], f"Expected truncated history, got {seqs}"
