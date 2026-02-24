"""Tests for event bus."""

from __future__ import annotations

import pytest

from grid.agentic.event_bus import EventBus
from grid.agentic.events import CaseCreatedEvent


@pytest.fixture
def event_bus():
    """Create event bus instance."""
    return EventBus(use_redis=False)


@pytest.mark.asyncio
async def test_publish_event(event_bus):
    """Test publishing an event."""
    event = CaseCreatedEvent(case_id="TEST-001", raw_input="Test")
    await event_bus.publish(event.to_dict())

    history = await event_bus.get_event_history()
    assert len(history) == 1


@pytest.mark.asyncio
async def test_subscribe_handler(event_bus):
    """Test subscribing to events."""
    received_events = []

    async def handler(event):
        received_events.append(event)

    await event_bus.subscribe("case.created", handler)

    event = CaseCreatedEvent(case_id="TEST-001", raw_input="Test")
    await event_bus.publish(event.to_dict())

    assert len(received_events) == 1
    assert received_events[0]["case_id"] == "TEST-001"


@pytest.mark.asyncio
async def test_subscribe_all_events(event_bus):
    """Test subscribing to all events."""
    received_events = []

    async def handler(event):
        received_events.append(event)

    await event_bus.subscribe_all(handler)

    from grid.agentic.events import CaseCreatedEvent, CaseExecutedEvent

    await event_bus.publish(CaseCreatedEvent(case_id="TEST-001", raw_input="Test").to_dict())
    await event_bus.publish(CaseExecutedEvent(case_id="TEST-001", agent_role="Executor", task="/execute").to_dict())

    assert len(received_events) == 2


@pytest.mark.asyncio
async def test_event_history_filtering(event_bus):
    """Test event history filtering."""
    from grid.agentic.events import CaseCreatedEvent, CaseExecutedEvent

    await event_bus.publish(CaseCreatedEvent(case_id="TEST-001", raw_input="Test").to_dict())
    await event_bus.publish(CaseExecutedEvent(case_id="TEST-001", agent_role="Executor", task="/execute").to_dict())
    await event_bus.publish(CaseCreatedEvent(case_id="TEST-002", raw_input="Test 2").to_dict())

    # Filter by event type
    created_events = await event_bus.get_event_history(event_type="case.created")
    assert len(created_events) == 2

    # Filter by limit
    recent = await event_bus.get_event_history(limit=2)
    assert len(recent) == 2


@pytest.mark.asyncio
async def test_event_replay(event_bus):
    """Test event replay."""
    from grid.agentic.events import CaseCreatedEvent

    await event_bus.publish(CaseCreatedEvent(case_id="TEST-001", raw_input="Test").to_dict())

    replay_count = []

    async def handler(event):
        replay_count.append(event)

    await event_bus.subscribe("case.created", handler)

    await event_bus.replay_events(event_type="case.created")

    # Handler should be called for replayed event
    assert len(replay_count) >= 1
