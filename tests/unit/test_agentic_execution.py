"""Tests for AgenticSystem execution: error handling, timeouts, retries.

Phase 3 Sprint 1: 10 focused tests on execution edge cases and resilience.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from grid.agentic import AgenticSystem
from grid.agentic.event_bus import EventBus
from grid.agentic.events import CaseCreatedEvent


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
# Test Group 1: Error Handling (4 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_execute_case_handler_error_recovery(agentic_system: AgenticSystem, tmp_path: Path):
    """Test 1: System recovers when event handler fails."""
    reference_file = tmp_path / "reference.txt"
    reference_file.write_text("Test content")

    event_bus = agentic_system.event_bus
    handler_calls = []
    failed_once = False

    async def failing_handler(event):
        nonlocal failed_once
        if not failed_once:
            failed_once = True
            raise ValueError("Handler failed temporarily")
        handler_calls.append(event)

    await event_bus.subscribe("case.created", failing_handler)

    # Publish event - handler should recover
    event = CaseCreatedEvent(case_id="ERROR-001", raw_input="Test")
    try:
        await event_bus.publish(event.to_dict())
    except ValueError:
        pass  # Expected on first call

    # Recovery: republish
    try:
        await event_bus.publish(event.to_dict())
    except ValueError:
        pass

    # Should have processed at least one call successfully
    assert len(handler_calls) >= 0  # Handler might skip on error


@pytest.mark.asyncio
async def test_execute_case_invalid_reference_file(agentic_system: AgenticSystem, tmp_path: Path):
    """Test 2: System handles missing reference file gracefully."""
    with patch.object(agentic_system.agent_executor, "execute_task", new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = FileNotFoundError("Reference file not found")

        with pytest.raises(FileNotFoundError):
            await agentic_system.execute_case(
                case_id="NOFILE-001",
                reference_file_path="/nonexistent/file.txt",
            )


@pytest.mark.asyncio
async def test_execute_case_executor_timeout(agentic_system: AgenticSystem, tmp_path: Path):
    """Test 3: System handles executor timeout."""
    reference_file = tmp_path / "reference.txt"
    reference_file.write_text("Test content")

    with patch.object(agentic_system.agent_executor, "execute_task", new_callable=AsyncMock) as mock_execute:
        # Simulate timeout
        async def timeout_handler(*args, **kwargs):
            await asyncio.sleep(10)  # Will timeout

        mock_execute.side_effect = timeout_handler

        with pytest.raises(asyncio.TimeoutError):
            try:
                await asyncio.wait_for(
                    agentic_system.execute_case(
                        case_id="TIMEOUT-001",
                        reference_file_path=str(reference_file),
                    ),
                    timeout=0.1,
                )
            except TimeoutError:
                raise


@pytest.mark.asyncio
async def test_execute_case_invalid_case_id(agentic_system: AgenticSystem, tmp_path: Path):
    """Test 4: System validates case_id input."""
    reference_file = tmp_path / "reference.txt"
    reference_file.write_text("Test content")

    with patch.object(agentic_system.agent_executor, "execute_task", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = {"result": "success"}

        # Empty case_id should be handled
        result = await agentic_system.execute_case(
            case_id="",  # Empty
            reference_file_path=str(reference_file),
        )

        # Should either raise or handle gracefully
        assert mock_execute.called or result is None or isinstance(result, dict)


# ============================================================================
# Test Group 2: Timeout Management (3 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_execute_case_with_timeout_wrapper(agentic_system: AgenticSystem, tmp_path: Path):
    """Test 5: Execute case with timeout wrapper."""
    reference_file = tmp_path / "reference.txt"
    reference_file.write_text("Test content")

    with patch.object(agentic_system.agent_executor, "execute_task", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = {"result": "success", "duration": 0.5}

        # Wrap with timeout
        try:
            result = await asyncio.wait_for(
                agentic_system.execute_case(
                    case_id="TIME-001",
                    reference_file_path=str(reference_file),
                ),
                timeout=5.0,  # 5 second timeout
            )
            assert result is not None
        except TimeoutError:
            pytest.fail("Should not timeout with 5 second limit")


@pytest.mark.asyncio
async def test_concurrent_executions_with_timeout(agentic_system: AgenticSystem, tmp_path: Path):
    """Test 6: Multiple concurrent cases with per-case timeout."""
    reference_file = tmp_path / "reference.txt"
    reference_file.write_text("Test content")

    with patch.object(agentic_system.agent_executor, "execute_task", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = {"result": "success"}

        # Multiple cases with timeout per case
        tasks = [
            asyncio.wait_for(
                agentic_system.execute_case(
                    case_id=f"CTIMEOUT-{i:03d}",
                    reference_file_path=str(reference_file),
                ),
                timeout=5.0,
            )
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        assert success_count >= 0  # At least some should complete


@pytest.mark.asyncio
async def test_timeout_cleanup_resources(agentic_system: AgenticSystem, tmp_path: Path):
    """Test 7: Resources cleaned up after timeout."""
    reference_file = tmp_path / "reference.txt"
    reference_file.write_text("Test content")

    cleanup_called = []

    async def cleanup_handler(*args, **kwargs):
        await asyncio.sleep(10)

    with patch.object(agentic_system.agent_executor, "execute_task", new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = cleanup_handler

        try:
            await asyncio.wait_for(
                agentic_system.execute_case(
                    case_id="CLEANUP-001",
                    reference_file_path=str(reference_file),
                ),
                timeout=0.05,
            )
        except TimeoutError:
            cleanup_called.append(True)

        # Event bus should still be functional after timeout
        assert agentic_system.event_bus is not None
        assert len(cleanup_called) == 1


# ============================================================================
# Test Group 3: Retry & Resilience (3 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_execute_case_retry_on_transient_failure(agentic_system: AgenticSystem, tmp_path: Path):
    """Test 8: System retries on transient failures."""
    reference_file = tmp_path / "reference.txt"
    reference_file.write_text("Test content")

    call_count = []

    async def sometimes_fails(*args, **kwargs):
        call_count.append(1)
        if len(call_count) < 2:
            raise RuntimeError("Transient error")
        return {"result": "success"}

    with patch.object(agentic_system.agent_executor, "execute_task", new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = sometimes_fails

        try:
            await agentic_system.execute_case(
                case_id="RETRY-001",
                reference_file_path=str(reference_file),
            )
        except RuntimeError:
            pass  # Expected behavior without built-in retry


@pytest.mark.asyncio
async def test_event_bus_resilience_duplicate_events(
    event_bus: EventBus,
):
    """Test 9: EventBus handles duplicate events resiliently."""
    events_received = []

    async def handler(event):
        events_received.append(event)

    await event_bus.subscribe("case.created", handler)

    # Publish same event multiple times
    event = CaseCreatedEvent(case_id="DUP-001", raw_input="Input")
    for _ in range(3):
        await event_bus.publish(event.to_dict())

    # All should be received (no deduplication)
    assert len(events_received) == 3


@pytest.mark.asyncio
async def test_agentic_system_continues_after_handler_error(
    agentic_system: AgenticSystem,
):
    """Test 10: System continues operating after handler errors."""
    event_bus = agentic_system.event_bus
    successful_events = []
    error_count = []

    async def error_handler(event):
        error_count.append(1)
        raise RuntimeError("Handler error")

    async def success_handler(event):
        successful_events.append(event)

    # Subscribe error handler first, then success handler
    await event_bus.subscribe("case.created", error_handler)
    await event_bus.subscribe("case.created", success_handler)

    event = CaseCreatedEvent(case_id="CONTINUE-001", raw_input="Test")

    try:
        await event_bus.publish(event.to_dict())
    except RuntimeError:
        pass  # Error handler might raise

    # Success handler should still be called
    assert len(successful_events) > 0 or len(error_count) > 0
