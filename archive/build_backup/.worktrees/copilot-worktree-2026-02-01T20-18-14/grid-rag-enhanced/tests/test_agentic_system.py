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
