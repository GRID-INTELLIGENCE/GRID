"""Tests for event handlers."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from grid.agentic.event_handlers import (
    CaseCategorizedHandler,
    CaseCompletedHandler,
    CaseCreatedHandler,
    EventHandlerRegistry,
)


@pytest.fixture
def mock_repository():
    """Create mock repository."""
    repo = AsyncMock()
    repo.create_case = AsyncMock()
    repo.update_case_status = AsyncMock()
    repo.get_case = AsyncMock(return_value={"case_id": "TEST-001", "structured_data": {}})
    return repo


@pytest.fixture
def mock_learning_system():
    """Create mock learning system."""
    learning = AsyncMock()
    learning.record_case_completion = AsyncMock()
    return learning


@pytest.mark.asyncio
async def test_case_created_handler(mock_repository):
    """Test CaseCreatedHandler."""
    handler = CaseCreatedHandler(repository=mock_repository)

    event = {
        "event_type": "case.created",
        "case_id": "TEST-001",
        "raw_input": "Test input",
        "user_id": "user123",
    }

    await handler.handle(event)

    mock_repository.create_case.assert_called_once()
    call_args = mock_repository.create_case.call_args
    assert call_args[1]["case_id"] == "TEST-001"
    assert call_args[1]["raw_input"] == "Test input"


@pytest.mark.asyncio
async def test_case_categorized_handler(mock_repository):
    """Test CaseCategorizedHandler."""
    handler = CaseCategorizedHandler(repository=mock_repository)

    event = {
        "event_type": "case.categorized",
        "case_id": "TEST-001",
        "category": "testing",
        "priority": "high",
        "confidence": 0.85,
        "structured_data": {},
    }

    await handler.handle(event)

    mock_repository.update_case_status.assert_called_once()
    call_args = mock_repository.update_case_status.call_args
    assert call_args[1]["case_id"] == "TEST-001"
    assert call_args[1]["status"] == "categorized"
    assert call_args[1]["category"] == "testing"


@pytest.mark.asyncio
async def test_case_completed_handler(mock_repository, mock_learning_system):
    """Test CaseCompletedHandler."""
    handler = CaseCompletedHandler(repository=mock_repository, learning_system=mock_learning_system)

    event = {
        "event_type": "case.completed",
        "case_id": "TEST-001",
        "outcome": "success",
        "solution": "Solution applied",
        "agent_experience": {"time_taken": "2 hours"},
    }

    await handler.handle(event)

    mock_repository.update_case_status.assert_called_once()
    mock_learning_system.record_case_completion.assert_called_once()


@pytest.mark.asyncio
async def test_event_handler_registry():
    """Test EventHandlerRegistry."""
    registry = EventHandlerRegistry()

    handler1_called = []
    handler2_called = []

    class TestHandler1:
        async def handle(self, event):
            handler1_called.append(event)

    class TestHandler2:
        async def handle(self, event):
            handler2_called.append(event)

    handler1 = TestHandler1()
    handler2 = TestHandler2()

    registry.register("case.created", handler1)
    registry.register("case.created", handler2)

    event = {"event_type": "case.created", "case_id": "TEST-001"}

    await registry.handle_event(event)

    assert len(handler1_called) == 1
    assert len(handler2_called) == 1
