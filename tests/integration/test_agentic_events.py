"""Tests for AgenticSystem event bus integration and async coordination.

Phase 3 Sprint 1: 15 focused tests on event-driven architecture.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
import pytest_asyncio

from grid.agentic import AgenticSystem
from grid.agentic.event_bus import EventBus
from grid.agentic.events import (
    CaseCategorizedEvent,
    CaseCompletedEvent,
    CaseCreatedEvent,
    CaseExecutedEvent,
    CaseReferenceGeneratedEvent,
)


@pytest_asyncio.fixture
async def event_bus() -> EventBus:
    """Create clean event bus for each test."""
    return EventBus(use_redis=False)


@pytest_asyncio.fixture
async def knowledge_base_path(tmp_path) -> Path:
    """Create temporary knowledge base."""
    kb_path = tmp_path / "knowledge_base"
    kb_path.mkdir()
    (kb_path / "receptionist.txt").write_text("Receptionist prompt")
    (kb_path / "lawyer.txt").write_text("Lawyer prompt")
    (kb_path / "executor.txt").write_text("Executor prompt")
    return kb_path


@pytest_asyncio.fixture
async def agentic_system(knowledge_base_path: Path, event_bus: EventBus) -> AgenticSystem:
    """Create AgenticSystem instance."""
    return AgenticSystem(
        knowledge_base_path=knowledge_base_path,
        event_bus=event_bus,
        repository=None,
        enable_cognitive=False,
    )


# ============================================================================
# Test Group 1: Event Subscription & Delivery (4 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_case_created_event_subscription(event_bus: EventBus):
    """Test 1: Subscribe to case.created events."""
    received = []

    async def handler(event):
        received.append(event)

    await event_bus.subscribe("case.created", handler)
    await event_bus.publish(CaseCreatedEvent(case_id="SUB-001", raw_input="Input").to_dict())

    assert len(received) == 1
    assert received[0]["case_id"] == "SUB-001"


@pytest.mark.asyncio
async def test_case_categorized_event_subscription(event_bus: EventBus):
    """Test 2: Subscribe to case.categorized events."""
    received = []

    async def handler(event):
        received.append(event)

    await event_bus.subscribe("case.categorized", handler)
    await event_bus.publish(
        CaseCategorizedEvent(
            case_id="CAT-001",
            category="legal",
            priority="high",
        ).to_dict()
    )

    assert len(received) == 1
    assert received[0]["category"] == "legal"


@pytest.mark.asyncio
async def test_case_reference_generated_event(event_bus: EventBus):
    """Test 3: Subscribe to case.reference_generated events."""
    received = []

    async def handler(event):
        received.append(event)

    await event_bus.subscribe("case.reference_generated", handler)
    await event_bus.publish(
        CaseReferenceGeneratedEvent(
            case_id="REF-001",
            reference_file_path="/path/to/ref.txt",
            recommended_roles=["lawyer", "executor"],
            recommended_tasks=["/analyze", "/execute"],
        ).to_dict()
    )

    assert len(received) == 1
    assert received[0]["case_id"] == "REF-001"


@pytest.mark.asyncio
async def test_multiple_event_subscriptions(event_bus: EventBus):
    """Test 4: Multiple subscriptions to same event type."""
    handlers_called = {"h1": [], "h2": [], "h3": []}

    async def handler1(event):
        handlers_called["h1"].append(event)

    async def handler2(event):
        handlers_called["h2"].append(event)

    async def handler3(event):
        handlers_called["h3"].append(event)

    await event_bus.subscribe("case.created", handler1)
    await event_bus.subscribe("case.created", handler2)
    await event_bus.subscribe("case.created", handler3)

    await event_bus.publish(CaseCreatedEvent(case_id="MULTI-001", raw_input="Input").to_dict())

    assert len(handlers_called["h1"]) == 1
    assert len(handlers_called["h2"]) == 1
    assert len(handlers_called["h3"]) == 1


# ============================================================================
# Test Group 2: Event Workflow Chains (4 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_receptionist_workflow_events(event_bus: EventBus):
    """Test 5: Receptionist workflow: created → categorized → reference."""
    events = []

    async def tracking_handler(event):
        events.append(event["event_type"])

    await event_bus.subscribe_all(tracking_handler)

    # Simulate receptionist workflow
    await event_bus.publish(CaseCreatedEvent(case_id="RECEP-001", raw_input="Legal inquiry").to_dict())
    await event_bus.publish(CaseCategorizedEvent(case_id="RECEP-001", category="legal", priority="high").to_dict())
    await event_bus.publish(
        CaseReferenceGeneratedEvent(
            case_id="RECEP-001",
            reference_file_path="/path/to/ref.txt",
            recommended_roles=["lawyer"],
            recommended_tasks=["/analyze"],
        ).to_dict()
    )

    assert "case.created" in events
    assert "case.categorized" in events
    assert "case.reference_generated" in events


@pytest.mark.asyncio
async def test_lawyer_workflow_events(event_bus: EventBus):
    """Test 6: Lawyer workflow: created → executed → completed."""
    events = []

    async def tracking_handler(event):
        events.append((event["case_id"], event["event_type"]))

    await event_bus.subscribe_all(tracking_handler)

    case_id = "LAWYER-001"

    # Simulate lawyer workflow
    await event_bus.publish(CaseCreatedEvent(case_id=case_id, raw_input="Document review").to_dict())
    await event_bus.publish(CaseExecutedEvent(case_id=case_id, agent_role="lawyer", task="/analyze").to_dict())
    await event_bus.publish(
        CaseCompletedEvent(case_id=case_id, outcome="success", solution="Analysis complete").to_dict()
    )

    case_events = [e for e in events if e[0] == case_id]
    assert len(case_events) == 3
    assert case_events[0][1] == "case.created"
    assert case_events[1][1] == "case.executed"
    assert case_events[2][1] == "case.completed"


@pytest.mark.asyncio
async def test_parallel_case_workflows(event_bus: EventBus):
    """Test 7: Parallel workflows for multiple cases."""
    events_by_case = {}

    async def tracking_handler(event):
        case_id = event.get("case_id")
        if case_id not in events_by_case:
            events_by_case[case_id] = []
        events_by_case[case_id].append(event["event_type"])

    await event_bus.subscribe_all(tracking_handler)

    # Simulate parallel case processing
    cases = ["PARALLEL-001", "PARALLEL-002", "PARALLEL-003"]
    for case_id in cases:
        await event_bus.publish(CaseCreatedEvent(case_id=case_id, raw_input="Input").to_dict())

    for case_id in cases:
        await event_bus.publish(CaseExecutedEvent(case_id=case_id, agent_role="lawyer", task="/process").to_dict())

    assert len(events_by_case) == 3
    for case_id in cases:
        assert case_id in events_by_case
        assert "case.created" in events_by_case[case_id]
        assert "case.executed" in events_by_case[case_id]


@pytest.mark.asyncio
async def test_event_order_preservation(event_bus: EventBus):
    """Test 8: Event order is preserved in delivery."""
    event_order = []

    async def tracking_handler(event):
        event_order.append(event["event_type"])

    await event_bus.subscribe_all(tracking_handler)

    # Publish events in specific order
    await event_bus.publish(CaseCreatedEvent(case_id="ORDER-001", raw_input="First").to_dict())
    await event_bus.publish(CaseCategorizedEvent(case_id="ORDER-001", category="A", priority="1").to_dict())
    await event_bus.publish(CaseExecutedEvent(case_id="ORDER-001", agent_role="lawyer", task="/a").to_dict())
    await event_bus.publish(CaseCompletedEvent(case_id="ORDER-001", outcome="success", solution="Done").to_dict())

    assert event_order == [
        "case.created",
        "case.categorized",
        "case.executed",
        "case.completed",
    ]


# ============================================================================
# Test Group 3: Async Coordination & Synchronization (4 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_concurrent_case_creation_events(event_bus: EventBus):
    """Test 9: Concurrent case creation events."""
    created_cases = []

    async def handler(event):
        created_cases.append(event["case_id"])

    await event_bus.subscribe("case.created", handler)

    # Publish multiple case creations concurrently
    tasks = [
        event_bus.publish(CaseCreatedEvent(case_id=f"CONCURRENT-{i:03d}", raw_input=f"Input {i}").to_dict())
        for i in range(10)
    ]

    await asyncio.gather(*tasks)
    assert len(created_cases) == 10


@pytest.mark.asyncio
async def test_event_handler_async_operations(event_bus: EventBus):
    """Test 10: Event handlers can perform async operations."""
    processing_results = []

    async def async_handler(event):
        # Simulate async processing
        await asyncio.sleep(0.01)
        processing_results.append({"case_id": event["case_id"], "processed": True})

    await event_bus.subscribe("case.created", async_handler)

    # Publish events
    for i in range(5):
        await event_bus.publish(CaseCreatedEvent(case_id=f"ASYNC-{i:03d}", raw_input="Input").to_dict())

    assert len(processing_results) == 5
    assert all(r["processed"] for r in processing_results)


@pytest.mark.asyncio
async def test_event_driven_case_state_synchronization(event_bus: EventBus):
    """Test 11: Event-driven state synchronization across handlers."""
    case_states = {}

    async def state_manager(event):
        case_id = event.get("case_id")
        if case_id not in case_states:
            case_states[case_id] = {"created": False, "executed": False, "completed": False}

        if event["event_type"] == "case.created":
            case_states[case_id]["created"] = True
        elif event["event_type"] == "case.executed":
            case_states[case_id]["executed"] = True
        elif event["event_type"] == "case.completed":
            case_states[case_id]["completed"] = True

    await event_bus.subscribe_all(state_manager)

    case_id = "SYNC-001"
    await event_bus.publish(CaseCreatedEvent(case_id=case_id, raw_input="Input").to_dict())
    await event_bus.publish(CaseExecutedEvent(case_id=case_id, agent_role="lawyer", task="/task").to_dict())
    await event_bus.publish(CaseCompletedEvent(case_id=case_id, outcome="success", solution="Done").to_dict())

    assert case_states[case_id]["created"]
    assert case_states[case_id]["executed"]
    assert case_states[case_id]["completed"]


@pytest.mark.asyncio
async def test_event_publisher_subscriber_coordination(event_bus: EventBus):
    """Test 12: Publisher and subscriber coordination without blocking."""
    publish_times = []
    subscribe_times = []

    async def handler(event):
        subscribe_times.append(event["case_id"])
        # Don't block subscriber

    await event_bus.subscribe("case.created", handler)

    # Publish rapidly without waiting for handlers
    tasks = []
    for i in range(10):
        publish_times.append(f"COORD-{i:03d}")
        tasks.append(event_bus.publish(CaseCreatedEvent(case_id=f"COORD-{i:03d}", raw_input="Input").to_dict()))

    await asyncio.gather(*tasks)

    # Both should have same count eventually
    assert len(publish_times) == 10
    assert len(subscribe_times) == 10


# ============================================================================
# Test Group 4: System Integration (3 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_agentic_system_event_emission_integration(agentic_system: AgenticSystem, event_bus: EventBus):
    """Test 13: AgenticSystem properly integrates with EventBus."""
    assert agentic_system.event_bus is event_bus

    events = []

    async def handler(event):
        events.append(event)

    await event_bus.subscribe_all(handler)

    # Publish event through system's bus
    await agentic_system.event_bus.publish(CaseCreatedEvent(case_id="INTEG-001", raw_input="Input").to_dict())

    assert len(events) == 1
    assert events[0]["case_id"] == "INTEG-001"


@pytest.mark.asyncio
async def test_event_replay_for_recovery(event_bus: EventBus):
    """Test 14: Event replay for system recovery scenarios."""
    # Publish initial events
    for i in range(5):
        await event_bus.publish(CaseCreatedEvent(case_id=f"REPLAY-{i:03d}", raw_input="Input").to_dict())

    # Get history
    history = await event_bus.get_event_history(event_type="case.created", limit=10)
    assert len(history) >= 5

    # Replay events (e.g., for recovery)
    replayed = []

    async def handler(event):
        replayed.append(event)

    await event_bus.subscribe("case.created", handler)
    await event_bus.replay_events(event_type="case.created", limit=5)

    assert len(replayed) > 0


@pytest.mark.asyncio
async def test_event_driven_monitoring(event_bus: EventBus):
    """Test 15: Event-driven monitoring and metrics collection."""
    metrics = {
        "created_count": 0,
        "executed_count": 0,
        "completed_count": 0,
        "total_cases": set(),
    }

    async def metrics_handler(event):
        case_id = event.get("case_id")
        if case_id:
            metrics["total_cases"].add(case_id)

        if event["event_type"] == "case.created":
            metrics["created_count"] += 1
        elif event["event_type"] == "case.executed":
            metrics["executed_count"] += 1
        elif event["event_type"] == "case.completed":
            metrics["completed_count"] += 1

    await event_bus.subscribe_all(metrics_handler)

    # Simulate workflow
    for i in range(5):
        case_id = f"METRIC-{i:03d}"
        await event_bus.publish(CaseCreatedEvent(case_id=case_id, raw_input="Input").to_dict())
        await event_bus.publish(CaseExecutedEvent(case_id=case_id, agent_role="lawyer", task="/task").to_dict())
        await event_bus.publish(CaseCompletedEvent(case_id=case_id, outcome="success", solution="Done").to_dict())

    assert metrics["created_count"] == 5
    assert metrics["executed_count"] == 5
    assert metrics["completed_count"] == 5
    assert len(metrics["total_cases"]) == 5
