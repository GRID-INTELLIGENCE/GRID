import os
import sys

import pytest

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src")))

from grid.agentic.event_bus import EventBus, Subscription


@pytest.mark.asyncio
async def test_agentic_event_bus_unsubscribe():
    """Test that agentic event bus supports unsubscription."""
    bus = EventBus()

    events_received = []
    async def handler(event):
        events_received.append(event)

    # 1. Subscribe
    sub = await bus.subscribe("agent.log", handler)
    assert isinstance(sub, Subscription)
    assert sub.id in bus._subscription_index
    assert sub in bus.handlers["agent.log"]

    # 2. Publish
    await bus.publish({"event_type": "agent.log", "msg": "hello"})
    assert len(events_received) == 1

    # 3. Unsubscribe
    res = await bus.unsubscribe(sub)
    assert res is True
    assert sub.id not in bus._subscription_index
    assert sub not in bus.handlers["agent.log"]

    # 4. Publish again
    await bus.publish({"event_type": "agent.log", "msg": "world"})
    assert len(events_received) == 1  # Still 1

@pytest.mark.asyncio
async def test_agentic_event_bus_unsubscribe_all():
    """Test unsubscription for subscribe_all."""
    bus = EventBus()

    counter = 0
    async def handler(event):
        nonlocal counter
        counter += 1

    sub = await bus.subscribe_all(handler)
    await bus.publish({"event_type": "any", "val": 1})
    assert counter == 1

    await bus.unsubscribe(sub.id)
    await bus.publish({"event_type": "any", "val": 2})
    assert counter == 1
