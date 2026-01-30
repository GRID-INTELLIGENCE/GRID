"""Tests for AgenticSystem core functionality.

Covers execute(), task management, state, and fundamental orchestration.
Phase 3 Sprint 1: 15 focused async tests.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from grid.agentic import AgenticSystem
from grid.agentic.event_bus import EventBus
from grid.agentic.events import CaseCompletedEvent, CaseCreatedEvent, CaseExecutedEvent


@pytest_asyncio.fixture
async def event_bus() -> EventBus:
    """Create clean event bus for each test."""
    return EventBus(use_redis=False)


@pytest_asyncio.fixture
async def knowledge_base_path(tmp_path) -> Path:
    """Create temporary knowledge base with sample agent files."""
    kb_path = tmp_path / "knowledge_base"
    kb_path.mkdir()
    (kb_path / "receptionist.txt").write_text("Receptionist agent prompt")
    (kb_path / "lawyer.txt").write_text("Lawyer agent prompt")
    (kb_path / "executor.txt").write_text("Executor agent prompt")
    return kb_path


@pytest_asyncio.fixture
async def agentic_system(knowledge_base_path: Path, event_bus: EventBus) -> AgenticSystem:
    """Create AgenticSystem instance for testing."""
    return AgenticSystem(
        knowledge_base_path=knowledge_base_path,
        event_bus=event_bus,
        repository=None,
        enable_cognitive=False,
    )


# ============================================================================
# Test Group 1: System Initialization (3 tests)
# ============================================================================


def test_agentic_system_init(knowledge_base_path: Path, event_bus: EventBus):
    """Test 1: System initializes with valid configuration."""
    system = AgenticSystem(
        knowledge_base_path=knowledge_base_path,
        event_bus=event_bus,
        enable_cognitive=False,
    )
    assert system is not None
    assert system.knowledge_base_path == knowledge_base_path
    assert system.event_bus is event_bus


def test_agentic_system_default_event_bus(knowledge_base_path: Path):
    """Test 2: System creates default event bus if not provided."""
    system = AgenticSystem(
        knowledge_base_path=knowledge_base_path,
        event_bus=None,
        enable_cognitive=False,
    )
    assert system.event_bus is not None
    assert isinstance(system.event_bus, EventBus)


@pytest.mark.asyncio
async def test_agentic_system_has_executor(agentic_system: AgenticSystem):
    """Test 3: System has agent executor available."""
    assert agentic_system.agent_executor is not None
    assert hasattr(agentic_system.agent_executor, "execute_task")


# ============================================================================
# Test Group 2: Case Execution (3 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_execute_case_basic(agentic_system: AgenticSystem, tmp_path: Path):
    """Test 4: System executes a case with required parameters."""
    reference_file = tmp_path / "reference.txt"
    reference_file.write_text("Test content")

    with patch.object(
        agentic_system.agent_executor, "execute_task", new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.return_value = {"result": "success"}

        result = await agentic_system.execute_case(
            case_id="TEST-001",
            reference_file_path=str(reference_file),
            agent_role="lawyer",
        )

        assert result is not None
        assert mock_execute.called


@pytest.mark.asyncio
async def test_execute_case_with_task(agentic_system: AgenticSystem, tmp_path: Path):
    """Test 5: System executes specific task when provided."""
    reference_file = tmp_path / "reference.txt"
    reference_file.write_text("Test content")

    with patch.object(
        agentic_system.agent_executor, "execute_task", new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.return_value = {"task_executed": "/analyze"}

        result = await agentic_system.execute_case(
            case_id="TASK-001",
            reference_file_path=str(reference_file),
            task="/analyze",
        )

        assert result is not None


@pytest.mark.asyncio
async def test_execute_case_with_user(agentic_system: AgenticSystem, tmp_path: Path):
    """Test 6: System tracks execution with user_id."""
    reference_file = tmp_path / "reference.txt"
    reference_file.write_text("Test content")

    with patch.object(
        agentic_system.agent_executor, "execute_task", new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.return_value = {"user": "alice"}

        result = await agentic_system.execute_case(
            case_id="USER-001",
            reference_file_path=str(reference_file),
            user_id="alice",
        )

        assert result is not None


# ============================================================================
# Test Group 3: Event Emission (4 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_case_created_event(event_bus: EventBus):
    """Test 7: CaseCreatedEvent emits and is delivered."""
    events = []

    async def handler(event):
        events.append(event)

    await event_bus.subscribe("case.created", handler)
    await event_bus.publish(
        CaseCreatedEvent(case_id="CREATE-001", raw_input="Test input").to_dict()
    )

    assert len(events) == 1
    assert events[0]["case_id"] == "CREATE-001"


@pytest.mark.asyncio
async def test_case_executed_event(event_bus: EventBus):
    """Test 8: CaseExecutedEvent emits and carries agent role."""
    events = []

    async def handler(event):
        events.append(event)

    await event_bus.subscribe("case.executed", handler)
    await event_bus.publish(
        CaseExecutedEvent(
            case_id="EXEC-001",
            agent_role="lawyer",
            task="/analyze",
        ).to_dict()
    )

    assert len(events) == 1
    assert events[0]["agent_role"] == "lawyer"


@pytest.mark.asyncio
async def test_case_completed_event(event_bus: EventBus):
    """Test 9: CaseCompletedEvent emits with outcome."""
    events = []

    async def handler(event):
        events.append(event)

    await event_bus.subscribe("case.completed", handler)
    await event_bus.publish(
        CaseCompletedEvent(
            case_id="COMPLETE-001",
            outcome="success",
            solution="Resolved successfully",
        ).to_dict()
    )

    assert len(events) == 1
    assert events[0]["outcome"] == "success"


@pytest.mark.asyncio
async def test_event_chain_sequence(event_bus: EventBus):
    """Test 10: Event chain: created → executed → completed."""
    events = []

    async def handler(event):
        events.append(event["event_type"])

    await event_bus.subscribe_all(handler)

    await event_bus.publish(
        CaseCreatedEvent(case_id="CHAIN-001", raw_input="Input").to_dict()
    )
    await event_bus.publish(
        CaseExecutedEvent(case_id="CHAIN-001", agent_role="lawyer", task="/task").to_dict()
    )
    await event_bus.publish(
        CaseCompletedEvent(
            case_id="CHAIN-001", outcome="success", solution="Done"
        ).to_dict()
    )

    assert len(events) == 3
    assert events == ["case.created", "case.executed", "case.completed"]


# ============================================================================
# Test Group 4: State & History (3 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_event_history_tracking(event_bus: EventBus):
    """Test 11: EventBus tracks event history."""
    await event_bus.publish(
        CaseCreatedEvent(case_id="STATE-001", raw_input="Input 1").to_dict()
    )
    await event_bus.publish(
        CaseCreatedEvent(case_id="STATE-002", raw_input="Input 2").to_dict()
    )

    history = await event_bus.get_event_history()
    assert len(history) >= 2


@pytest.mark.asyncio
async def test_event_history_filtering(event_bus: EventBus):
    """Test 12: EventBus filters history by type."""
    await event_bus.publish(
        CaseCreatedEvent(case_id="FILTER-001", raw_input="Input").to_dict()
    )
    await event_bus.publish(
        CaseCreatedEvent(case_id="FILTER-002", raw_input="Input").to_dict()
    )
    await event_bus.publish(
        CaseExecutedEvent(case_id="FILTER-001", agent_role="lawyer", task="/task").to_dict()
    )

    created = await event_bus.get_event_history(event_type="case.created")
    executed = await event_bus.get_event_history(event_type="case.executed")

    assert len(created) == 2
    assert len(executed) == 1


@pytest.mark.asyncio
async def test_event_replay(event_bus: EventBus):
    """Test 13: EventBus replays events from history."""
    replayed = []

    async def handler(event):
        replayed.append(event)

    for i in range(3):
        await event_bus.publish(
            CaseCreatedEvent(case_id=f"REPLAY-{i:03d}", raw_input="Input").to_dict()
        )

    await event_bus.subscribe("case.created", handler)
    await event_bus.replay_events(event_type="case.created", limit=3)

    assert len(replayed) > 0


# ============================================================================
# Test Group 5: Concurrency (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_concurrent_cases(agentic_system: AgenticSystem, tmp_path: Path):
    """Test 14: System handles multiple cases concurrently."""
    reference_file = tmp_path / "reference.txt"
    reference_file.write_text("Test content")

    with patch.object(
        agentic_system.agent_executor, "execute_task", new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.return_value = {"result": "success"}

        tasks = [
            agentic_system.execute_case(
                case_id=f"CONCURRENT-{i:03d}",
                reference_file_path=str(reference_file),
            )
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)
        assert len(results) == 5


@pytest.mark.asyncio
async def test_concurrent_event_publishing(event_bus: EventBus):
    """Test 15: EventBus handles concurrent event publishing."""
    events = []

    async def handler(event):
        events.append(event)

    await event_bus.subscribe_all(handler)

    tasks = [
        event_bus.publish(
            CaseCreatedEvent(
                case_id=f"CONC-{i:03d}",
                raw_input=f"Input {i}",
            ).to_dict()
        )
        for i in range(10)
    ]

    await asyncio.gather(*tasks)
    assert len(events) == 10
