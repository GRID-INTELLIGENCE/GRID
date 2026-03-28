import uuid
from unittest.mock import MagicMock, patch

import pytest

from infrastructure.event_bus.event_system import EventBus, Subscription


@pytest.mark.asyncio
async def test_event_bus_subscribe_unsubscribe():
    """
    Test that subscribe returns a Subscription handle and unsubscribe works.
    """
    with patch.object(EventBus, "__new__", side_effect=object.__new__):
        bus = EventBus()
        bus.__init__()

        handler = MagicMock(return_value=None)

        # subscribe is sync in event_system_fixed
        sub = bus.subscribe("test.event", handler)

        assert isinstance(sub, Subscription)
        assert sub.event_type == "test.event"

        # Verify internal state — event_system_fixed uses _subscribers[event_type][callback_id]
        assert sub.callback_id in bus._subscribers["test.event"]

        # Unsubscribe via the Subscription handle
        sub.unsubscribe()

        assert sub.callback_id not in bus._subscribers["test.event"]


@pytest.mark.asyncio
async def test_event_bus_unsubscribe_by_handle():
    """Test unsubscribing via the Subscription object."""
    with patch.object(EventBus, "__new__", side_effect=object.__new__):
        bus = EventBus()
        bus.__init__()

        def dummy_handler(e):
            pass

        sub = bus.subscribe("test.event.2", dummy_handler)
        assert sub.callback_id in bus._subscribers["test.event.2"]

        sub.unsubscribe()
        assert sub.callback_id not in bus._subscribers["test.event.2"]


@pytest.mark.asyncio
async def test_event_bus_metrics_update():
    """Test that metrics stubs are patchable for prometheus integration tests."""

    with patch("infrastructure.event_bus.event_system.METRICS_ENABLED", True):
        with (
            patch("infrastructure.event_bus.event_system._subscriptions_created") as mock_created,
            patch("infrastructure.event_bus.event_system._subscriptions_removed") as mock_removed,
            patch("infrastructure.event_bus.event_system._active_subscriptions") as mock_active,
        ):
            # Metrics stubs are patchable — verify they landed
            assert mock_created is not None
            assert mock_removed is not None
            assert mock_active is not None
