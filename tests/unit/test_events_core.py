"""
Unit tests for GRID Event System core module.

Tests cover:
- Event data structure and properties
- EventBus subscription and emission
- EventStore persistence and querying
- Middleware pipeline
- Priority-based dispatch
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta

import pytest

from grid.events.core import (
    Event,
    EventBus,
    EventPriority,
    EventStore,
    LoggingMiddleware,
    TimingMiddleware,
    ValidationMiddleware,
    emit,
    get_event_bus,
    subscribe,
)


class TestEvent:
    """Tests for Event data structure."""

    def test_event_creation(self):
        """Event should be created with required fields."""
        event = Event(
            type="test:event",
            data={"key": "value"},
            source="test_source",
        )
        assert event.type == "test:event"
        assert event.data == {"key": "value"}
        assert event.source == "test_source"
        assert event.correlation_id is not None
        assert event.event_id is not None
        assert event.priority == EventPriority.NORMAL

    def test_event_with_causation(self):
        """Event should support causation tracking."""
        parent = Event(type="parent", data={}, source="test")
        child = parent.spawn_child("child", {"data": "value"}, "test")
        assert child.causation_id == parent.event_id
        assert child.correlation_id == parent.correlation_id

    def test_event_serialization(self):
        """Event should serialize to/from dict."""
        event = Event(type="test", data={"key": "value"}, source="test")
        event_dict = event.to_dict()
        restored = Event.from_dict(event_dict)
        assert restored.type == event.type
        assert restored.data == event.data
        assert restored.correlation_id == event.correlation_id

    def test_event_age(self):
        """Event should track age correctly."""
        event = Event(type="test", data={}, source="test")
        time.sleep(0.01)
        assert event.age_ms > 10

    def test_event_hash(self):
        """Event should be hashable."""
        event = Event(type="test", data={}, source="test")
        hash_value = hash(event)
        assert isinstance(hash_value, int)


class TestEventStore:
    """Tests for EventStore persistence."""

    def test_store_and_retrieve(self):
        """Store should persist and retrieve events."""
        store = EventStore(max_events=100)
        event = Event(type="test", data={"key": "value"}, source="test")

        store.append(event)
        assert event.correlation_id is not None, "Event should have a correlation_id"
        retrieved = store.get_by_correlation(event.correlation_id)
        assert len(retrieved) == 1
        assert retrieved[0].event_id == event.event_id

    def test_event_eviction(self):
        """Store should evict oldest events when at capacity."""
        store = EventStore(max_events=3)
        for i in range(5):
            store.append(Event(type=f"event_{i}", data={}, source="test"))

        assert len(store) == 3
        recent = store.get_recent(10)
        assert recent[0].type == "event_2"

    def test_time_range_query(self):
        """Store should query by time range."""
        store = EventStore()
        now = datetime.now()

        event1 = Event(type="test1", data={}, source="test", timestamp=now - timedelta(minutes=10))
        event2 = Event(type="test2", data={}, source="test", timestamp=now)

        store.append(event1)
        store.append(event2)

        results = store.get_by_time_range(now - timedelta(minutes=5), now)
        assert len(results) == 1
        assert results[0].type == "test2"

    def test_type_index(self):
        """Store should index by event type."""
        store = EventStore()
        event = Event(type="test:event", data={}, source="test")
        store.append(event)

        retrieved = store.get_by_type("test:event")
        assert len(retrieved) == 1
        assert retrieved[0].event_id == event.event_id

    def test_clear(self):
        """Store should clear all events."""
        store = EventStore()
        store.append(Event(type="test", data={}, source="test"))
        store.clear()
        assert len(store) == 0


class TestEventBus:
    """Tests for EventBus dispatch."""

    def test_subscribe_and_emit(self):
        """Bus should deliver events to subscribers."""
        bus = EventBus(store_events=False)
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("test:*", handler)
        bus.emit(Event(type="test:event", data={}, source="test"))

        assert len(received) == 1
        assert received[0].type == "test:event"

    def test_wildcard_subscription(self):
        """Bus should support wildcard patterns."""
        bus = EventBus(store_events=False)
        received = []

        def handler(event):
            received.append(event.type)

        bus.subscribe("test:*", handler)
        bus.emit(Event(type="test:one", data={}, source="test"))
        bus.emit(Event(type="test:two", data={}, source="test"))
        bus.emit(Event(type="other:event", data={}, source="test"))

        assert len(received) == 2
        assert "test:one" in received
        assert "test:two" in received

    def test_priority_dispatch(self):
        """Bus should dispatch by priority order."""
        bus = EventBus(store_events=False)
        order = []

        def low_handler(event):
            order.append("low")

        def high_handler(event):
            order.append("high")

        bus.subscribe("test:*", low_handler, priority=EventPriority.LOW)
        bus.subscribe("test:*", high_handler, priority=EventPriority.HIGH)
        bus.emit(Event(type="test:event", data={}, source="test"))

        assert order == ["high", "low"]

    def test_unsubscribe(self):
        """Bus should allow unsubscribing."""
        bus = EventBus(store_events=False)
        received = []

        def handler(event):
            received.append(event)

        sub_id = bus.subscribe("test:*", handler)
        bus.unsubscribe(sub_id)
        bus.emit(Event(type="test:event", data={}, source="test"))

        assert len(received) == 0

    def test_one_time_subscription(self):
        """Bus should support one-time subscriptions."""
        bus = EventBus(store_events=False)
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("test:*", handler, once=True)
        bus.emit(Event(type="test:event", data={}, source="test"))
        bus.emit(Event(type="test:event", data={}, source="test"))

        assert len(received) == 1

    def test_middleware_pipeline(self):
        """Bus should apply middleware to events."""
        bus = EventBus(store_events=False)
        bus.add_middleware(TimingMiddleware())

        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("test:*", handler)
        bus.emit(Event(type="test:event", data={}, source="test"))

        assert len(received) == 1
        assert "received_at" in received[0].metadata

    def test_decorator_subscription(self):
        """Bus should support decorator syntax."""
        bus = EventBus(store_events=False)
        received = []

        @bus.on("test:*")
        def handler(event):
            received.append(event)

        bus.emit(Event(type="test:event", data={}, source="test"))
        assert len(received) == 1

    def test_error_handling(self):
        """Bus should handle handler errors gracefully."""
        bus = EventBus(store_events=False)

        def failing_handler(event):
            raise ValueError("Test error")

        bus.subscribe("test:*", failing_handler)
        bus.emit(Event(type="test:event", data={}, source="test"))

        stats = bus.get_stats()
        assert stats["errors"] > 0

    def test_event_store_integration(self):
        """Bus should store events when enabled."""
        bus = EventBus(store_events=True)
        event = Event(type="test", data={}, source="test")

        bus.emit(event)

        store = bus.get_event_store()
        assert store is not None
        assert len(store) > 0

    def test_filter_function(self):
        """Bus should support filter functions."""
        bus = EventBus(store_events=False)
        received = []

        def handler(event):
            received.append(event)

        def filter_fn(event):
            return event.data.get("allowed", False)

        bus.subscribe("test:*", handler, filter_fn=filter_fn)
        bus.emit(Event(type="test:1", data={"allowed": True}, source="test"))
        bus.emit(Event(type="test:2", data={"allowed": False}, source="test"))

        assert len(received) == 1


class TestMiddleware:
    """Tests for middleware components."""

    def test_logging_middleware(self):
        """LoggingMiddleware should log events."""
        middleware = LoggingMiddleware()
        event = Event(type="test", data={}, source="test")
        result = middleware.process(event)
        assert result.type == "test"

    def test_timing_middleware(self):
        """TimingMiddleware should add timing metadata."""
        middleware = TimingMiddleware()
        event = Event(type="test", data={}, source="test")
        result = middleware.process(event)
        assert "received_at" in result.metadata
        assert "event_age_ms" in result.metadata

    def test_validation_middleware(self):
        """ValidationMiddleware should validate events."""
        middleware = ValidationMiddleware()

        # Valid event
        event = Event(type="test", data={}, source="test")
        result = middleware.process(event)
        assert result.correlation_id is not None

        # Invalid event (no type)
        with pytest.raises(ValueError):
            middleware.process(Event(type="", data={}, source="test"))


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_get_event_bus_singleton(self):
        """get_event_bus should return singleton instance."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_emit_function(self):
        """emit function should use default bus."""
        received = []

        def handler(event):
            received.append(event)

        subscribe("test:*", handler)
        emit(Event(type="test:event", data={}, source="test"))

        assert len(received) == 1
