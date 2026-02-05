import uuid
from unittest.mock import MagicMock, patch

import pytest

from infrastructure.event_bus.event_system import EventBus, Subscription


@pytest.mark.asyncio
async def test_event_bus_subscribe_unsubscribe():
    """
    Test that the new subscribe returns a Subscription handle and unsubscribe works.
    """
    # Allow instantiation for testing
    with patch.object(EventBus, "__new__", side_effect=object.__new__):
        bus = EventBus()
        bus.__init__()

        # Mock handlers
        handler = MagicMock(return_value=None)

        # Subscribe
        sub = await bus.subscribe("test.event", handler)

        assert isinstance(sub, Subscription)
        assert sub.event_type == "test.event"
        assert sub.handler == handler
        assert isinstance(sub.id, uuid.UUID)

        # Verify internal state (using the actual internal attributes)
        # Note: EventBus stores Subscription objects in _subscribers
        assert sub in bus._subscribers["test.event"]
        assert sub.id in bus._index

        # Unsubscribe
        result = await bus.unsubscribe(sub)
        assert result is True

        # Verify removal
        assert sub not in bus._subscribers["test.event"]
        assert sub.id not in bus._index

        # Unsubscribe again (idempotence/safety)
        result_retry = await bus.unsubscribe(sub)
        assert result_retry is False

@pytest.mark.asyncio
async def test_event_bus_unsubscribe_by_id():
    """Test unsubscribing using only the UUID."""
    with patch.object(EventBus, "__new__", side_effect=object.__new__):
        bus = EventBus()
        bus.__init__()

        async def dummy_handler(e): pass

        sub = await bus.subscribe("test.event.2", dummy_handler)
        assert sub.id in bus._index

        result = await bus.unsubscribe(sub.id)
        assert result is True
        assert sub.id not in bus._index
        assert sub not in bus._subscribers["test.event.2"]

@pytest.mark.asyncio
async def test_event_bus_metrics_update():
    """Test that metrics are updated (if prometheus_client is waiting)."""

    with patch("infrastructure.event_bus.event_system.METRICS_ENABLED", True):
        with patch("infrastructure.event_bus.event_system._subscriptions_created") as mock_created, \
             patch("infrastructure.event_bus.event_system._subscriptions_removed") as mock_removed, \
             patch("infrastructure.event_bus.event_system._active_subscriptions") as mock_active:

            with patch.object(EventBus, "__new__", side_effect=object.__new__):
                bus = EventBus()
                bus.__init__()

                async def h(e): pass

                sub = await bus.subscribe("m.event", h)

                mock_created.inc.assert_called()
                mock_active.labels.assert_called_with(event_type="m.event")
                mock_active.labels.return_value.inc.assert_called()

                await bus.unsubscribe(sub)

                mock_removed.inc.assert_called()
                mock_active.labels.return_value.dec.assert_called()
