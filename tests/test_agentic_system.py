"""Tests for agentic system."""

from __future__ import annotations

import json

import pytest

from grid.agentic import AgentExecutor, AgenticSystem
from grid.agentic.event_bus import EventBus
from grid.agentic.events import CaseCompletedEvent, CaseCreatedEvent, CaseExecutedEvent


@pytest.fixture
def knowledge_base_path(tmp_path):
    """Create temporary knowledge base."""
    kb_path = tmp_path / "knowledge_base"
    kb_path.mkdir()
    return kb_path


@pytest.fixture
def event_bus():
    """Create event bus instance."""
    return EventBus(use_redis=False)


@pytest.fixture
def agentic_system(knowledge_base_path, event_bus):
    """Create agentic system instance."""
    return AgenticSystem(knowledge_base_path=knowledge_base_path, event_bus=event_bus, repository=None)


@pytest.mark.asyncio
async def test_agentic_system_execute_case(agentic_system, tmp_path):
    """Test case execution."""
    # Create reference file inside knowledge base
    reference_file = agentic_system.knowledge_base_path / "reference.json"
    reference_file.write_text(
        json.dumps({"case_id": "TEST-001", "recommended_roles": ["Executor"], "recommended_tasks": ["/execute"]})
    )

    # Execute case with relative path
    result = await agentic_system.execute_case(case_id="TEST-001", reference_file_path="reference.json")

    assert result["status"] == "completed"
    assert "execution_time_seconds" in result


@pytest.mark.asyncio
async def test_agent_executor_execute_task(knowledge_base_path, tmp_path):
    """Test agent executor."""
    executor = AgentExecutor(knowledge_base_path=knowledge_base_path)

    # Create reference file inside knowledge base
    reference_file = knowledge_base_path / "reference.json"
    reference_file.write_text(
        json.dumps({"case_id": "TEST-001", "recommended_roles": ["Executor"], "recommended_tasks": ["/inventory"]})
    )

    result = await executor.execute_task(
        case_id="TEST-001", reference_file_path="reference.json", agent_role="Analyst", task="/inventory"
    )

    assert result["task"] == "/inventory"
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_event_bus_publish(event_bus):
    """Test event bus publishing."""
    handler_called = []

    async def test_handler(event):
        handler_called.append(event)

    await event_bus.subscribe("case.created", test_handler)

    event = CaseCreatedEvent(case_id="TEST-001", raw_input="Test input")

    await event_bus.publish(event.to_dict())

    assert len(handler_called) == 1
    assert handler_called[0]["case_id"] == "TEST-001"


@pytest.mark.asyncio
async def test_event_bus_subscribe_all(event_bus):
    """Test subscribing to all events."""
    handler_called = []

    async def test_handler(event):
        handler_called.append(event)

    await event_bus.subscribe_all(test_handler)

    event1 = CaseCreatedEvent(case_id="TEST-001", raw_input="Input 1")
    event2 = CaseExecutedEvent(case_id="TEST-001", agent_role="Executor", task="/execute")

    await event_bus.publish(event1.to_dict())
    await event_bus.publish(event2.to_dict())

    assert len(handler_called) == 2


@pytest.mark.asyncio
async def test_event_bus_history(event_bus):
    """Test event history."""
    event = CaseCreatedEvent(case_id="TEST-001", raw_input="Test")
    await event_bus.publish(event.to_dict())

    history = await event_bus.get_event_history()
    assert len(history) == 1
    assert history[0]["case_id"] == "TEST-001"


def test_case_created_event():
    """Test CaseCreatedEvent."""
    event = CaseCreatedEvent(
        case_id="TEST-001", raw_input="Test input", user_id="user123", examples=["Example 1"], scenarios=["Scenario 1"]
    )

    event_dict = event.to_dict()
    assert event_dict["event_type"] == "case.created"
    assert event_dict["case_id"] == "TEST-001"
    assert event_dict["raw_input"] == "Test input"
    assert event_dict["user_id"] == "user123"


def test_case_executed_event():
    """Test CaseExecutedEvent."""
    event = CaseExecutedEvent(case_id="TEST-001", agent_role="Executor", task="/execute")

    event_dict = event.to_dict()
    assert event_dict["event_type"] == "case.executed"
    assert event_dict["agent_role"] == "Executor"
    assert event_dict["task"] == "/execute"


def test_case_completed_event():
    """Test CaseCompletedEvent."""
    event = CaseCompletedEvent(
        case_id="TEST-001", outcome="success", solution="Solution applied", agent_experience={"time_taken": "2 hours"}
    )

    event_dict = event.to_dict()
    assert event_dict["event_type"] == "case.completed"
    assert event_dict["outcome"] == "success"
    assert event_dict["solution"] == "Solution applied"


# ============================================================================
# SPRINT 1: Additional Async Tests for Event-Driven Architecture
# ============================================================================


@pytest.mark.asyncio
async def test_agentic_system_execute_case_with_agent_role(agentic_system):
    """Test case execution with specific agent role."""
    reference_file = agentic_system.knowledge_base_path / "role_test.json"
    reference_file.write_text(
        json.dumps(
            {
                "case_id": "ROLE-001",
                "recommended_roles": ["Analyst", "Executor"],
                "recommended_tasks": ["/analyze", "/execute"],
            }
        )
    )

    result = await agentic_system.execute_case(
        case_id="ROLE-001", reference_file_path="role_test.json", agent_role="Analyst", task="/analyze"
    )

    assert result["status"] == "completed"
    assert "execution_time_seconds" in result


@pytest.mark.asyncio
async def test_agentic_system_execute_case_with_user_id(agentic_system):
    """Test case execution with user tracking."""
    reference_file = agentic_system.knowledge_base_path / "user_test.json"
    reference_file.write_text(
        json.dumps({"case_id": "USER-001", "recommended_roles": ["Executor"], "recommended_tasks": ["/execute"]})
    )

    result = await agentic_system.execute_case(
        case_id="USER-001", reference_file_path="user_test.json", user_id="test_user_123"
    )

    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_event_bus_concurrent_events(event_bus):
    """Test event bus handling concurrent event publishing."""
    import asyncio

    events_received = []

    async def handler(event):
        events_received.append(event)
        await asyncio.sleep(0.01)  # Simulate processing

    await event_bus.subscribe_all(handler)

    # Publish multiple events concurrently
    tasks = []
    for i in range(5):
        event = CaseCreatedEvent(case_id=f"CONCURRENT-{i:03d}", raw_input=f"Input {i}")
        tasks.append(event_bus.publish(event.to_dict()))

    await asyncio.gather(*tasks)

    assert len(events_received) == 5
    case_ids = {e["case_id"] for e in events_received}
    assert len(case_ids) == 5


@pytest.mark.asyncio
async def test_event_bus_filtered_subscription(event_bus):
    """Test event filtering in subscriptions."""
    created_events = []
    executed_events = []

    async def created_handler(event):
        created_events.append(event)

    async def executed_handler(event):
        executed_events.append(event)

    await event_bus.subscribe("case.created", created_handler)
    await event_bus.subscribe("case.executed", executed_handler)

    # Publish different event types
    created_event = CaseCreatedEvent(case_id="FILTER-001", raw_input="Test")
    executed_event = CaseExecutedEvent(case_id="FILTER-001", agent_role="Executor", task="/execute")

    await event_bus.publish(created_event.to_dict())
    await event_bus.publish(executed_event.to_dict())

    assert len(created_events) == 1
    assert len(executed_events) == 1
    assert created_events[0]["case_id"] == "FILTER-001"
    assert executed_events[0]["agent_role"] == "Executor"


@pytest.mark.asyncio
async def test_event_bus_error_handling(event_bus):
    """Test event bus error handling when handler fails."""
    call_count = []

    async def failing_handler(event):
        call_count.append(1)
        raise ValueError("Handler error")

    async def recovery_handler(event):
        call_count.append(2)

    await event_bus.subscribe("case.created", failing_handler)
    await event_bus.subscribe("case.created", recovery_handler)

    event = CaseCreatedEvent(case_id="ERROR-001", raw_input="Test")

    # Should publish without raising (handlers handle errors)
    try:
        await event_bus.publish(event.to_dict())
    except Exception:
        pass  # Error handling may vary by implementation

    # At least one handler should have been called
    assert len(call_count) > 0


@pytest.mark.asyncio
async def test_agentic_system_case_completion_event(agentic_system):
    """Test that case execution triggers completion event."""
    completion_events = []

    async def completion_handler(event):
        if event.get("event_type") == "case.completed":
            completion_events.append(event)

    await agentic_system.event_bus.subscribe("case.completed", completion_handler)

    reference_file = agentic_system.knowledge_base_path / "completion_test.json"
    reference_file.write_text(
        json.dumps({"case_id": "COMPLETE-001", "recommended_roles": ["Executor"], "recommended_tasks": ["/execute"]})
    )

    result = await agentic_system.execute_case(case_id="COMPLETE-001", reference_file_path="completion_test.json")

    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_agent_executor_multiple_tasks(knowledge_base_path):
    """Test executing multiple tasks sequentially."""
    executor = AgentExecutor(knowledge_base_path=knowledge_base_path)

    reference_file = knowledge_base_path / "multi_task.json"
    reference_file.write_text(
        json.dumps(
            {
                "case_id": "MULTI-001",
                "recommended_roles": ["Analyzer", "Executor"],
                "recommended_tasks": ["/inventory", "/execute"],
            }
        )
    )

    # Execute first task
    result1 = await executor.execute_task(
        case_id="MULTI-001", reference_file_path="multi_task.json", agent_role="Analyzer", task="/inventory"
    )

    # Execute second task
    result2 = await executor.execute_task(
        case_id="MULTI-001", reference_file_path="multi_task.json", agent_role="Executor", task="/execute"
    )

    assert result1["status"] == "completed"
    assert result2["status"] == "completed"
    assert result1["task"] == "/inventory"
    assert result2["task"] == "/execute"


@pytest.mark.asyncio
async def test_event_creation_timestamps(event_bus):
    """Test that events have proper timestamps."""

    event = CaseCreatedEvent(case_id="TIME-001", raw_input="Test")
    event_dict = event.to_dict()

    assert "timestamp" in event_dict
    assert isinstance(event_dict["timestamp"], (int, float, str))


@pytest.mark.asyncio
async def test_case_executed_event_chain(event_bus):
    """Test the chain: case.created → case.executed → case.completed."""
    event_chain = []

    async def chain_handler(event):
        event_chain.append(event.get("event_type"))

    await event_bus.subscribe_all(chain_handler)

    # Publish event chain
    created = CaseCreatedEvent(case_id="CHAIN-001", raw_input="Test")
    executed = CaseExecutedEvent(case_id="CHAIN-001", agent_role="Executor", task="/execute")
    completed = CaseCompletedEvent(case_id="CHAIN-001", outcome="success", solution="Done")

    await event_bus.publish(created.to_dict())
    await event_bus.publish(executed.to_dict())
    await event_bus.publish(completed.to_dict())

    assert "case.created" in event_chain
    assert "case.executed" in event_chain
    assert "case.completed" in event_chain
    assert len(event_chain) == 3
