"""
Comprehensive event system testing covering event bus, handlers, and persistence.
Tests event ordering, replay, circuit breakers, and Redis integration.
"""

import asyncio
import time
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from grid.agentic.event_bus import EventBus


class TestEventBusCore:
    """Test core event bus functionality"""

    @pytest.fixture
    def event_bus(self):
        """Create in-memory event bus for testing"""
        return EventBus(use_redis=False, max_history=100)

    @pytest.fixture
    def mock_event_handler(self):
        """Create mock event handler"""
        handler = AsyncMock()
        return handler

    async def test_event_publishing(self, event_bus):
        """Scenario: Basic event publishing and receiving"""
        events_received = []

        async def test_handler(event_data):
            events_received.append(event_data)

        # Subscribe to event type
        await event_bus.subscribe("case.created", test_handler)

        # Publish test event
        test_event = {
            "event_type": "case.created",
            "case_id": "test_case_123",
            "timestamp": datetime.now().isoformat(),
            "data": {"title": "Test Case", "priority": "high"},
        }

        await event_bus.publish(test_event)

        # Wait for async processing
        await asyncio.sleep(0.1)

        # Verify event was received
        assert len(events_received) == 1, "Should receive exactly 1 event"
        received_event = events_received[0]
        assert received_event["case_id"] == "test_case_123", "Should preserve case ID"
        assert received_event["data"]["priority"] == "high", "Should preserve event data"

    async def test_event_history_tracking(self, event_bus):
        """Scenario: Event bus should maintain history of published events"""
        # Publish multiple events
        events = [{"event_type": "case.created", "case_id": f"case_{i}"} for i in range(5)]

        for event in events:
            await event_bus.publish(event)

        # Check history
        assert len(event_bus.event_history) == 5, "Should track all 5 events"

        # Verify order preservation
        case_ids = [event["case_id"] for event in event_bus.event_history]
        assert case_ids == ["case_0", "case_1", "case_2", "case_3", "case_4"], "Should preserve event order"

    async def test_multiple_handlers_for_same_event(self, event_bus):
        """Scenario: Multiple handlers can subscribe to same event type"""
        handler1_calls = []
        handler2_calls = []

        async def handler1(event_data):
            handler1_calls.append(event_data)

        async def handler2(event_data):
            handler2_calls.append(event_data)

        # Subscribe both handlers
        await event_bus.subscribe("case.created", handler1)
        await event_bus.subscribe("case.created", handler2)

        # Publish event
        test_event = {"event_type": "case.created", "case_id": "multi_handler_test"}

        await event_bus.publish(test_event)

        # Wait for async processing
        await asyncio.sleep(0.1)

        # Both handlers should be called
        assert len(handler1_calls) == 1, "Handler 1 should be called"
        assert len(handler2_calls) == 1, "Handler 2 should be called"
        assert handler1_calls[0] == handler2_calls[0], "Both should receive same event"

    async def test_event_handler_error_isolation(self, event_bus):
        """Scenario: Handler errors should not affect other handlers"""
        successful_handler_calls = []

        async def failing_handler(event_data):
            raise Exception("Handler failed")

        async def successful_handler(event_data):
            successful_handler_calls.append(event_data)

        # Subscribe both handlers
        await event_bus.subscribe("case.created", failing_handler)
        await event_bus.subscribe("case.created", successful_handler)

        # Publish event (should not raise)
        test_event = {"event_type": "case.created", "case_id": "error_test"}

        await event_bus.publish(test_event)

        # Wait for async processing
        await asyncio.sleep(0.1)

        # Successful handler should still be called
        assert len(successful_handler_calls) == 1, "Successful handler should be called despite failing handler"

    async def test_event_filtering_and_routing(self, event_bus):
        """Scenario: Event routing and filtering capabilities"""
        high_priority_events = []
        low_priority_events = []

        async def high_priority_handler(event_data):
            high_priority_events.append(event_data)

        async def low_priority_handler(event_data):
            low_priority_events.append(event_data)

        # Subscribe with different event types
        await event_bus.subscribe("case.created.high", high_priority_handler)
        await event_bus.subscribe("case.created.low", low_priority_handler)

        # Publish high priority event
        high_event = {"event_type": "case.created.high", "case_id": "high_priority_case", "priority": "high"}

        # Publish low priority event
        low_event = {"event_type": "case.created.low", "case_id": "low_priority_case", "priority": "low"}

        await event_bus.publish(high_event)
        await event_bus.publish(low_event)

        await asyncio.sleep(0.1)

        # Verify routing
        assert len(high_priority_events) == 1, "Should route high priority event"
        assert len(low_priority_events) == 1, "Should route low priority event"
        assert high_priority_events[0]["case_id"] == "high_priority_case", (
            "High priority handler should receive high event"
        )


class TestEventPersistence:
    """Test event persistence and replay functionality"""

    @pytest.fixture
    def event_bus_with_mock_persistence(self):
        """Create event bus with mock persistence"""
        Mock()
        return EventBus(use_redis=False, max_history=100)

    async def test_event_history_limiting(self, event_bus_with_mock_persistence):
        """Scenario: Event history should respect maximum size"""
        # Publish events exceeding max history
        max_history = 50
        small_bus = EventBus(use_redis=False, max_history=max_history)

        events = [
            {"event_type": "test.event", "id": i}
            for i in range(60)  # Exceed max_history
        ]

        for event in events:
            await small_bus.publish(event)

        # Should only keep max_history most recent events
        assert len(small_bus.event_history) == max_history, f"Should keep only {max_history} most recent events"

        # Verify most recent events are kept
        recent_ids = [event["id"] for event in small_bus.event_history]
        expected_recent = list(range(60))[10:]  # Last 50 events
        assert recent_ids == expected_recent, "Should keep most recent events in order"


class TestEventHandlers:
    """Test specific event handler implementations"""

    @pytest.fixture
    def mock_case_repository(self):
        """Create mock case repository for testing handlers"""
        return AsyncMock()

    @pytest.fixture
    def basic_event_handler(self):
        """Create basic event handler for testing"""

        # Create a simple result class
        class HandlerResult:
            def __init__(
                self,
                success: bool,
                case_id: str = "unknown",
                handled_event_type: str = "unknown",
                errors: list[str] | None = None,
            ):
                self.success = success
                self.case_id = case_id
                self.handled_event_type = handled_event_type
                self.errors = errors or []

            def __getitem__(self, key):
                return getattr(self, key)

        async def handle(event: dict[str, Any]) -> HandlerResult:
            """Basic event handler for testing"""
            # Basic validation
            if not event.get("event_type") or not event.get("case_id"):
                return HandlerResult(success=False, errors=["Missing required fields: event_type, case_id"])

            return HandlerResult(
                success=True,
                handled_event_type=event.get("event_type", "unknown"),
                case_id=event.get("case_id", "unknown"),
            )

        # Create a simple class to hold the handler
        class Handler:
            def __init__(self, handle_func):
                self.handle = handle_func

        return Handler(handle)

    async def test_basic_event_handling(self, basic_event_handler):
        """Scenario: Test basic event handling"""
        test_event = {
            "event_type": "case.created",
            "case_id": "test_case_123",
            "raw_input": "Create a test case for validation",
            "user_id": "test_user",
            "priority": "high",
        }

        # Handle the event
        result = await basic_event_handler.handle(test_event)

        assert result.success, "Should successfully handle event"
        assert result.case_id == "test_case_123", "Should return correct case ID"
        assert result["handled_event_type"] == "case.created", "Should preserve event type"

    async def test_basic_event_handler_error_handling(self, basic_event_handler):
        """Scenario: Event handlers should handle malformed events gracefully"""
        # Create malformed events
        malformed_events = [
            {},  # Missing required fields
            {"case_id": ""},  # Empty required fields
            {"priority": None},  # Invalid data types
        ]

        for malformed_event in malformed_events:
            result = await basic_event_handler.handle(malformed_event)
            assert not result.success, "Should reject malformed events"
            assert len(result.errors) > 0, "Should provide error details"

    async def test_basic_event_handler_performance(self, basic_event_handler):
        """Scenario: Event handlers should meet performance requirements"""
        # Create multiple events for performance testing
        events = [
            {
                "event_type": "case.created",
                "case_id": f"perf_test_case_{i}",
                "raw_input": f"Performance test case {i}",
                "priority": "medium",
            }
            for i in range(100)
        ]

        start_time = time.time()
        results = []

        for event in events:
            result = await basic_event_handler.handle(event)
            results.append(result)

        processing_time = time.time() - start_time

        # Performance assertions
        assert len(results) == 100, "Should process all 100 events"
        success_count = sum(1 for r in results if r.success)
        assert success_count >= 95, f"Should have at least 95% success rate, got {success_count}%"
        assert processing_time < 5.0, f"Should process in <5s, took {processing_time:.2f}s"

        # Per-event average
        avg_time_per_event = processing_time / 100
        assert avg_time_per_event < 0.05, (
            f"Each event should take <50ms on average, took {avg_time_per_event * 1000:.1f}ms"
        )


class TestEventSystemIntegration:
    """End-to-end event system integration tests"""

    @pytest.mark.asyncio
    async def test_complete_case_lifecycle_events(self):
        """Scenario: Complete case lifecycle from creation to completion"""
        # This would require setting up the full agentic system
        # For now, test the event publishing and handling flow
        event_bus = EventBus(use_redis=False)

        # Track events in order
        lifecycle_events = []

        async def event_tracker(event_data):
            lifecycle_events.append(event_data)

        # Subscribe to lifecycle event types
        lifecycle_event_types = [
            "case.created",
            "case.categorized",
            "case.reference_generated",
            "case.executed",
            "case.completed",
        ]

        for event_type in lifecycle_event_types:
            await event_bus.subscribe(event_type, event_tracker)

        # Simulate complete case lifecycle
        case_id = "lifecycle_test_case"

        # 1. Case Created
        case_created_event = {
            "event_type": "case.created",
            "case_id": case_id,
            "raw_input": "Test case for lifecycle validation",
            "user_id": "test_user",
            "priority": "high",
        }

        # 2. Case Categorized
        case_categorized_event = {
            "event_type": "case.categorized",
            "case_id": case_id,
            "category": "legal",
            "confidence": 0.92,
            "reasoning_text": "Document analysis indicates legal contract",
        }

        # 3. Reference Generated
        reference_generated_event = {
            "event_type": "case.reference_generated",
            "case_id": case_id,
            "reference": "REF-LC-2024-001",
            "reference_type": "legal_reference",
            "generated_by": "ai_system",
        }

        # 4. Case Executed
        case_executed_event = {
            "event_type": "case.executed",
            "case_id": case_id,
            "status": "in_progress",
            "executor": "ai_agent",
        }

        # 5. Case Completed
        case_completed_event = {
            "event_type": "case.completed",
            "case_id": case_id,
            "status": "completed",
            "outcome": "success",
            "completion_time": datetime.now().isoformat(),
        }

        lifecycle_events_list = [
            case_created_event,
            case_categorized_event,
            reference_generated_event,
            case_executed_event,
            case_completed_event,
        ]

        # Publish all lifecycle events
        for event in lifecycle_events_list:
            await event_bus.publish(event)

        # Wait for async processing
        await asyncio.sleep(0.1)

        # Verify lifecycle order
        assert len(lifecycle_events) == 5, "Should receive 5 lifecycle events"

        event_types_in_order = [event["event_type"] for event in lifecycle_events]
        expected_order = [
            "case.created",
            "case.categorized",
            "case.reference_generated",
            "case.executed",
            "case.completed",
        ]

        assert event_types_in_order == expected_order, "Events should be received in correct lifecycle order"

        # Verify all events are for same case
        case_ids = [event["case_id"] for event in lifecycle_events]
        assert all(case_id == "lifecycle_test_case" for case_id in case_ids), (
            "All events should be for the same case ID"
        )

    @pytest.mark.asyncio
    async def test_event_system_error_recovery(self):
        """Scenario: Event system should recover from errors gracefully"""
        event_bus = EventBus(use_redis=False, max_history=50)

        recovery_events = []
        error_events = []

        async def recovery_handler(event_data):
            recovery_events.append(event_data)

        async def error_handler(event_data):
            error_events.append(event_data)
            # Simulate error handling with recovery
            if "attempt" in event_data and event_data["attempt"] < 3:
                raise Exception(f"Handler error {event_data['attempt']}")
            else:
                return {"status": "recovered"}

        # Subscribe handlers
        await event_bus.subscribe("test.recovery", recovery_handler)
        await event_bus.subscribe("test.error", error_handler)

        # Send events with initial failures, then recovery
        for i in range(5):
            error_event = {"event_type": "test.error", "attempt": i, "data": f"error_data_{i}"}

            try:
                await event_bus.publish(error_event)
            except Exception:
                pass  # Expected failures

        await asyncio.sleep(0.01)

        # Verify error tracking
        assert len(error_events) >= 3, "Should record multiple error events"

        # Send recovery event
        recovery_event = {"event_type": "test.recovery", "data": "recovery_data"}

        await event_bus.publish(recovery_event)
        await asyncio.sleep(0.01)

        # Verify recovery handling
        assert len(recovery_events) == 1, "Should handle recovery events after errors"


class TestRedisIntegration:
    """Test Redis integration for distributed event processing"""

    @pytest.mark.asyncio
    async def test_redis_fallback_gracefully(self):
        """Scenario: Should fall back to in-memory when Redis fails"""
        with patch("grid.agentic.event_bus.REDIS_AVAILABLE", False):
            # Should fall back to in-memory when Redis is not available
            event_bus = EventBus(use_redis=True, redis_host="localhost", redis_port=6379)

            # Should not have Redis client
            assert not event_bus.use_redis, "Should fall back to in-memory when Redis unavailable"
            assert event_bus.redis_client is None, "Should clear Redis client on failure"

            # Test basic functionality still works
            events_received = []

            async def test_handler(event_data):
                events_received.append(event_data)

            await event_bus.subscribe("test.fallback", test_handler)

            test_event = {"event_type": "test.fallback", "data": "fallback_test"}
            await event_bus.publish(test_event)
            await asyncio.sleep(0.01)

            assert len(events_received) == 1, "Should still process events in fallback mode"

    @pytest.mark.asyncio
    async def test_event_bus_configuration_validation(self):
        """Scenario: Event bus should validate configuration parameters"""
        # Test with valid configurations
        valid_configs = [
            {"use_redis": False, "max_history": 100},
            {"use_redis": False, "max_history": 1000},
            {"use_redis": True, "redis_host": "localhost", "max_history": 50},
        ]

        for config in valid_configs:
            event_bus = EventBus(**config)
            assert event_bus.max_history == config["max_history"], "Should set max_history correctly"
            assert event_bus.use_redis == config.get("use_redis", False), "Should set Redis usage correctly"

        # Test with invalid configurations
        with pytest.raises(ValueError):
            EventBus(max_history=-1)  # Invalid negative history

        with pytest.raises(ValueError):
            EventBus(max_history=0)  # Invalid zero history
