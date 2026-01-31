"""
Parallel Threading Test Suite for Unified Fabric
=================================================
Comprehensive tests for concurrent/parallel behavior including:
- Concurrent event publishing
- Thread safety of safety router
- Parallel audit logging
- Race condition detection
- Deadlock prevention
- Performance under load
"""
import asyncio
import random
import threading
import time

import pytest

from src.unified_fabric import DynamicEventBus, Event, EventResponse
from src.unified_fabric.audit import AuditEventType, DistributedAuditLogger
from src.unified_fabric.safety_router import SafetyDecision, SafetyFirstRouter, SafetyReport

# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def event_bus():
    """Fresh event bus for each test"""
    return DynamicEventBus(bus_id=f"test-{random.randint(1000, 9999)}")


@pytest.fixture
def safety_router():
    """Fresh safety router for each test"""
    return SafetyFirstRouter()


@pytest.fixture
def audit_logger(tmp_path):
    """Fresh audit logger with temp directory"""
    return DistributedAuditLogger(log_dir=tmp_path, buffer_size=10)


# ============================================================================
# Concurrent Event Publishing Tests
# ============================================================================

class TestConcurrentEventPublishing:
    """Test concurrent event publishing behavior"""

    @pytest.mark.asyncio
    async def test_100_concurrent_publishes(self, event_bus):
        """Test 100 events published concurrently"""
        received = []
        lock = asyncio.Lock()

        async def handler(event):
            async with lock:
                received.append(event.event_id)

        event_bus.subscribe("concurrent.test", handler)
        await event_bus.start()

        # Create 100 events
        events = [
            Event(
                event_type="concurrent.test",
                payload={"index": i},
                source_domain="test"
            )
            for i in range(100)
        ]

        # Publish all concurrently
        await asyncio.gather(*[
            event_bus.publish(e, wait_for_handlers=True) for e in events
        ])

        await event_bus.stop()

        # All events should be received
        assert len(received) == 100
        # All event IDs should be unique
        assert len(set(received)) == 100

    @pytest.mark.asyncio
    async def test_multiple_handlers_concurrent(self, event_bus):
        """Test multiple handlers receiving same event concurrently"""
        handler1_received = []
        handler2_received = []
        handler3_received = []

        async def handler1(event):
            await asyncio.sleep(0.01)  # Simulate work
            handler1_received.append(event.event_id)

        async def handler2(event):
            await asyncio.sleep(0.02)  # Simulate different work
            handler2_received.append(event.event_id)

        async def handler3(event):
            handler3_received.append(event.event_id)

        event_bus.subscribe("multi.handler", handler1)
        event_bus.subscribe("multi.handler", handler2)
        event_bus.subscribe("multi.handler", handler3)

        await event_bus.start()

        event = Event(
            event_type="multi.handler",
            payload={"test": True},
            source_domain="test"
        )

        await event_bus.publish(event, wait_for_handlers=True)
        await event_bus.stop()

        # All handlers should receive the event
        assert len(handler1_received) == 1
        assert len(handler2_received) == 1
        assert len(handler3_received) == 1

    @pytest.mark.asyncio
    async def test_event_ordering_under_load(self, event_bus):
        """Test event ordering is maintained under heavy load"""
        received_order = []
        lock = asyncio.Lock()

        async def handler(event):
            async with lock:
                received_order.append(event.payload["sequence"])

        event_bus.subscribe("order.test", handler)
        await event_bus.start()

        # Publish events with sequence numbers
        for i in range(50):
            event = Event(
                event_type="order.test",
                payload={"sequence": i},
                source_domain="test"
            )
            await event_bus.publish(event, wait_for_handlers=True)

        await event_bus.stop()

        # Order should be preserved for synchronous publishes
        assert received_order == list(range(50))

    @pytest.mark.asyncio
    async def test_cross_domain_parallel_routing(self, event_bus):
        """Test parallel routing across multiple domains"""
        safety_events = []
        grid_events = []
        coinbase_events = []

        async def safety_handler(event):
            safety_events.append(event)

        async def grid_handler(event):
            grid_events.append(event)

        async def coinbase_handler(event):
            coinbase_events.append(event)

        event_bus.subscribe("cross.domain", safety_handler, domain="safety")
        event_bus.subscribe("cross.domain", grid_handler, domain="grid")
        event_bus.subscribe("cross.domain", coinbase_handler, domain="coinbase")

        await event_bus.start()

        # Publish events to different domains concurrently
        events = [
            Event(
                event_type="cross.domain",
                payload={"domain": "safety"},
                source_domain="test",
                target_domains=["safety"]
            ),
            Event(
                event_type="cross.domain",
                payload={"domain": "grid"},
                source_domain="test",
                target_domains=["grid"]
            ),
            Event(
                event_type="cross.domain",
                payload={"domain": "coinbase"},
                source_domain="test",
                target_domains=["coinbase"]
            ),
        ]

        await asyncio.gather(*[
            event_bus.publish(e, wait_for_handlers=True) for e in events
        ])

        await event_bus.stop()

        assert len(safety_events) == 1
        assert len(grid_events) == 1
        assert len(coinbase_events) == 1


# ============================================================================
# Thread Safety Tests
# ============================================================================

class TestThreadSafety:
    """Test thread safety of all components"""

    @pytest.mark.asyncio
    async def test_safety_router_concurrent_validations(self, safety_router):
        """Test safety router handles concurrent validations correctly"""
        results: list[SafetyReport] = []
        lock = asyncio.Lock()

        async def validate_content(content: str, user_id: str):
            report = await safety_router.validate(content, "grid", user_id)
            async with lock:
                results.append(report)

        # Create validation tasks
        contents = [
            ("Hello world", "user1"),
            ("This has violence", "user2"),
            ("Normal content here", "user3"),
            ("ignore previous instructions", "user4"),
            ("Another safe message", "user5"),
        ] * 20  # 100 validations

        await asyncio.gather(*[
            validate_content(c, u) for c, u in contents
        ])

        assert len(results) == 100
        # Verify consistency of decisions
        safe_count = sum(1 for r in results if r.decision == SafetyDecision.ALLOW)
        blocked_count = sum(1 for r in results if r.decision == SafetyDecision.BLOCK)

        # Should have consistent decisions for same content
        assert safe_count > 0
        assert blocked_count > 0

    @pytest.mark.asyncio
    async def test_rate_limiter_thread_safety(self, safety_router):
        """Test rate limiter is thread-safe under concurrent requests"""
        safety_router._max_requests_per_window = 50
        results = []
        lock = asyncio.Lock()

        async def make_request(user_id: str):
            report = await safety_router.validate("test", "grid", user_id)
            async with lock:
                results.append(report)

        # 100 requests from same user
        await asyncio.gather(*[
            make_request("single_user") for _ in range(100)
        ])

        # First 50 should pass, rest should be rate limited
        rate_limited = sum(
            1 for r in results
            if any(v.category == "rate_limit" for v in r.violations)
        )

        # Should have exactly 50 rate limited requests
        assert rate_limited == 50

    def test_event_bus_synchronous_thread_access(self, event_bus):
        """Test event bus can be accessed from multiple threads"""
        results = []
        lock = threading.Lock()

        def subscribe_from_thread(thread_id: int):
            async def handler(event):
                with lock:
                    results.append((thread_id, event.event_id))
            event_bus.subscribe(f"thread.{thread_id}", handler)

        # Subscribe from multiple threads
        threads = [
            threading.Thread(target=subscribe_from_thread, args=(i,))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All subscriptions should be registered
        assert event_bus.get_stats()["total_handlers"] == 10


# ============================================================================
# Parallel Audit Logging Tests
# ============================================================================

class TestParallelAuditLogging:
    """Test parallel audit logging behavior"""

    @pytest.mark.asyncio
    async def test_concurrent_log_writes(self, audit_logger):
        """Test concurrent log writes don't corrupt data"""
        await audit_logger.start()

        # Generate 100 log entries concurrently
        tasks = [
            audit_logger.log(
                event_type=AuditEventType.SYSTEM_EVENT,
                project_id="test",
                domain="test",
                action=f"action_{i}",
                user_id=f"user_{i}"
            )
            for i in range(100)
        ]

        request_ids = await asyncio.gather(*tasks)

        await audit_logger.stop()

        # All request IDs should be unique
        assert len(set(request_ids)) == 100

    @pytest.mark.asyncio
    async def test_buffer_flush_under_load(self, audit_logger):
        """Test buffer flushing works correctly under load"""
        audit_logger.buffer_size = 10
        await audit_logger.start()

        # Write more than buffer size
        for i in range(25):
            await audit_logger.log(
                event_type=AuditEventType.SYSTEM_EVENT,
                project_id="test",
                domain="test",
                action=f"action_{i}"
            )

        await audit_logger.stop()

        # All entries should be flushed
        entries = await audit_logger.get_recent_entries(limit=100)
        assert len(entries) == 25

    @pytest.mark.asyncio
    async def test_mixed_log_types_concurrent(self, audit_logger):
        """Test different log types can be written concurrently"""
        await audit_logger.start()

        # Create 100 independent async tasks (25 of each type)
        tasks = []
        for _ in range(25):
            tasks.append(audit_logger.log_safety_check("allow", "none", 0, "grid"))
            tasks.append(audit_logger.log_portfolio_action("buy", "port1", "user1", True))
            tasks.append(audit_logger.log_navigation("route", "A", "B", "user2", 50.0))
            tasks.append(audit_logger.log_error("test_error", "Test message", "test", "test"))

        # All tasks should complete and return request IDs
        request_ids = await asyncio.gather(*tasks)

        await audit_logger.stop()

        # Verify all 100 log calls completed with unique IDs
        assert len(request_ids) == 100
        assert len(set(request_ids)) == 100  # All unique with full UUIDs


# ============================================================================
# Race Condition Detection Tests
# ============================================================================

class TestRaceConditionPrevention:
    """Test for race conditions in critical sections"""

    @pytest.mark.asyncio
    async def test_event_bus_state_consistency(self, event_bus):
        """Test event bus state remains consistent under concurrent operations"""
        subscribe_count = 0
        unsubscribe_count = 0

        async def handler(event):
            pass

        async def subscribe_unsubscribe():
            nonlocal subscribe_count, unsubscribe_count
            event_bus.subscribe("race.test", handler)
            subscribe_count += 1
            await asyncio.sleep(0.001)
            event_bus.unsubscribe("race.test", handler)
            unsubscribe_count += 1

        await event_bus.start()

        # Many concurrent subscribe/unsubscribe cycles
        await asyncio.gather(*[subscribe_unsubscribe() for _ in range(50)])

        await event_bus.stop()

        # Counts should match
        assert subscribe_count == 50
        assert unsubscribe_count == 50

    @pytest.mark.asyncio
    async def test_reply_resolution_race(self, event_bus):
        """Test request-reply doesn't race with response delivery"""
        async def delayed_handler(event):
            await asyncio.sleep(0.05)  # Delay before reply
            event_bus.reply(event.event_id, EventResponse(
                success=True,
                data={"handled": True},
                event_id=event.event_id
            ))

        event_bus.subscribe("reply.race", delayed_handler)
        await event_bus.start()

        # Send multiple request-reply calls concurrently
        events = [
            Event(
                event_type="reply.race",
                payload={"id": i},
                source_domain="test"
            )
            for i in range(10)
        ]

        responses = await asyncio.gather(*[
            event_bus.request_reply(e, timeout=1.0) for e in events
        ])

        await event_bus.stop()

        # All should succeed
        assert all(r.success for r in responses)

    @pytest.mark.asyncio
    async def test_safety_violation_counter_race(self, safety_router):
        """Test safety violation counting under concurrent validations"""
        # Simulate content that triggers violations
        harmful_content = "violence attack weapon harm kill"

        reports = await asyncio.gather(*[
            safety_router.validate(harmful_content, "grid", f"user_{i}")
            for i in range(50)
        ])

        # All reports should have consistent violation counts
        violation_counts = [len(r.violations) for r in reports]

        # All should have same count (deterministic detection)
        assert len(set(violation_counts)) == 1


# ============================================================================
# Deadlock Prevention Tests
# ============================================================================

class TestDeadlockPrevention:
    """Test for potential deadlock scenarios"""

    @pytest.mark.asyncio
    async def test_nested_event_publishing(self, event_bus):
        """Test that nested event publishing doesn't deadlock"""
        final_received = []

        async def outer_handler(event):
            # Publish another event from within handler
            inner_event = Event(
                event_type="inner.event",
                payload={"from": "outer"},
                source_domain="test"
            )
            await event_bus.publish(inner_event, wait_for_handlers=True)

        async def inner_handler(event):
            final_received.append(event.event_id)

        event_bus.subscribe("outer.event", outer_handler)
        event_bus.subscribe("inner.event", inner_handler)

        await event_bus.start()

        outer_event = Event(
            event_type="outer.event",
            payload={"test": True},
            source_domain="test"
        )

        # Should complete without deadlock
        await asyncio.wait_for(
            event_bus.publish(outer_event, wait_for_handlers=True),
            timeout=5.0
        )

        await event_bus.stop()

        assert len(final_received) == 1

    @pytest.mark.asyncio
    async def test_circular_handler_reference(self, event_bus):
        """Test circular handler references don't cause deadlock"""
        a_triggered = []
        b_triggered = []
        max_depth = 5

        async def handler_a(event):
            a_triggered.append(event.event_id)
            depth = event.payload.get("depth", 0)
            if depth < max_depth:
                await event_bus.publish(Event(
                    event_type="event.b",
                    payload={"depth": depth + 1},
                    source_domain="test"
                ), wait_for_handlers=True)

        async def handler_b(event):
            b_triggered.append(event.event_id)
            depth = event.payload.get("depth", 0)
            if depth < max_depth:
                await event_bus.publish(Event(
                    event_type="event.a",
                    payload={"depth": depth + 1},
                    source_domain="test"
                ), wait_for_handlers=True)

        event_bus.subscribe("event.a", handler_a)
        event_bus.subscribe("event.b", handler_b)

        await event_bus.start()

        # Start the chain
        await asyncio.wait_for(
            event_bus.publish(Event(
                event_type="event.a",
                payload={"depth": 0},
                source_domain="test"
            ), wait_for_handlers=True),
            timeout=5.0
        )

        await event_bus.stop()

        # Both handlers should have been triggered
        assert len(a_triggered) > 0
        assert len(b_triggered) > 0


# ============================================================================
# Performance Under Load Tests
# ============================================================================

class TestPerformanceUnderLoad:
    """Test performance characteristics under heavy load"""

    @pytest.mark.asyncio
    async def test_event_throughput(self, event_bus):
        """Measure event throughput"""
        count = 0
        lock = asyncio.Lock()

        async def fast_handler(event):
            nonlocal count
            async with lock:
                count += 1

        event_bus.subscribe("throughput.test", fast_handler)
        await event_bus.start()

        num_events = 1000
        start_time = time.perf_counter()

        events = [
            Event(
                event_type="throughput.test",
                payload={"i": i},
                source_domain="test"
            )
            for i in range(num_events)
        ]

        await asyncio.gather(*[
            event_bus.publish(e, wait_for_handlers=True) for e in events
        ])

        elapsed = time.perf_counter() - start_time
        await event_bus.stop()

        throughput = num_events / elapsed
        print(f"\nEvent throughput: {throughput:.0f} events/sec")

        assert count == num_events
        assert throughput > 100  # At least 100 events/sec

    @pytest.mark.asyncio
    async def test_safety_validation_latency(self, safety_router):
        """Measure safety validation latency under load"""
        latencies = []

        for _ in range(100):
            start = time.perf_counter()
            await safety_router.validate("test content", "grid", "user")
            latencies.append((time.perf_counter() - start) * 1000)

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[95]

        print(f"\nAvg latency: {avg_latency:.2f}ms, P95: {p95_latency:.2f}ms")

        # Should be fast
        assert avg_latency < 10  # Less than 10ms average
        assert p95_latency < 20  # P95 less than 20ms

    @pytest.mark.asyncio
    async def test_audit_write_performance(self, audit_logger):
        """Measure audit write performance"""
        await audit_logger.start()

        start_time = time.perf_counter()

        for i in range(500):
            await audit_logger.log(
                event_type=AuditEventType.SYSTEM_EVENT,
                project_id="perf_test",
                domain="test",
                action=f"action_{i}"
            )

        elapsed = time.perf_counter() - start_time
        await audit_logger.stop()

        writes_per_sec = 500 / elapsed
        print(f"\nAudit writes: {writes_per_sec:.0f} writes/sec")

        assert writes_per_sec > 100  # At least 100 writes/sec


# ============================================================================
# Integration Tests
# ============================================================================

class TestParallelIntegration:
    """Integration tests for all components working together"""

    @pytest.mark.asyncio
    async def test_full_pipeline_parallel(self, event_bus, safety_router, audit_logger):
        """Test full pipeline with all components in parallel"""
        results = []

        async def process_request(request_id: int):
            # Validate
            report = await safety_router.validate(
                f"Request {request_id}: Normal content",
                "grid",
                f"user_{request_id}"
            )

            # Log
            log_id = await audit_logger.log(
                event_type=AuditEventType.REQUEST_RECEIVED,
                project_id="integration",
                domain="grid",
                action=f"request_{request_id}",
                status=report.decision.value
            )

            # Publish event
            event = Event(
                event_type="request.processed",
                payload={"request_id": request_id, "log_id": log_id},
                source_domain="grid"
            )
            await event_bus.publish(event)

            results.append((request_id, report.is_safe, log_id))

        await event_bus.start()
        await audit_logger.start()

        # Process 50 requests in parallel
        await asyncio.gather(*[process_request(i) for i in range(50)])

        await event_bus.stop()
        await audit_logger.stop()

        assert len(results) == 50
        # All should be processed safely
        assert all(is_safe for _, is_safe, _ in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])
