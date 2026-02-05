"""Tests for Parasite Guard integration with EventBus and DB engine."""

import asyncio
import sys
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Fix import path - add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from grid.security.parasite_guard import ParasiteContext, ParasiteStatus, PrunerOrchestrator


@pytest.mark.asyncio
async def test_parasite_context_cleanup_with_subscription() -> None:
    """Test that ParasiteContext cleanup handles EventBus subscription."""
    # Create a mock subscription
    subscription = MagicMock()
    subscription.id = uuid.uuid4()

    # Create context with subscription
    context = ParasiteContext(
        id=uuid.uuid4(),
        rule="test_rule",
        subscription=subscription,
    )

    # Mock the unsubscribe function by patching the module import
    mock_unsubscribe = AsyncMock()
    with patch.dict("sys.modules", {
        "infrastructure.event_bus.event_system": MagicMock(unsubscribe=mock_unsubscribe)
    }):
        await context.cleanup()

        # Verify unsubscribe was called
        mock_unsubscribe.assert_called_once_with(subscription)


@pytest.mark.asyncio
async def test_parasite_context_cleanup_hooks() -> None:
    """Test that ParasiteContext cleanup executes cleanup hooks."""
    hook_called = False

    async def async_hook() -> None:
        nonlocal hook_called
        hook_called = True

    sync_hook_called = False

    def sync_hook() -> None:
        nonlocal sync_hook_called
        sync_hook_called = True

    # Create context with cleanup hooks
    context = ParasiteContext(
        id=uuid.uuid4(),
        rule="test_rule",
        cleanup_hooks=[async_hook, sync_hook],
    )

    await context.cleanup()

    # Verify both hooks were called
    assert hook_called
    assert sync_hook_called


@pytest.mark.asyncio
async def test_parasite_context_cleanup_hooks_exception_handling() -> None:
    """Test that cleanup hooks handle exceptions gracefully."""
    async def failing_hook() -> None:
        raise RuntimeError("Hook failed")

    hook_called = False

    async def working_hook() -> None:
        nonlocal hook_called
        hook_called = True

    # Create context with mixed hooks
    context = ParasiteContext(
        id=uuid.uuid4(),
        rule="test_rule",
        cleanup_hooks=[failing_hook, working_hook],
    )

    # Should not raise exception
    await context.cleanup()

    # Verify working hook was still called
    assert hook_called


@pytest.mark.asyncio
async def test_pruner_disposes_database_engine() -> None:
    """Test that PrunerOrchestrator disposes database engine."""
    # Create pruner
    pruner = PrunerOrchestrator(app=None)
    steps = []

    # Mock dispose_async_engine
    with patch("application.mothership.db.engine.dispose_async_engine", new_callable=AsyncMock) as mock_dispose:
        await pruner._dispose_database_engine(steps)

        # Verify dispose was called
        mock_dispose.assert_called_once()

        # Verify steps were updated
        assert "Database engine disposed successfully" in steps


@pytest.mark.asyncio
async def test_pruner_handles_database_disposal_failure() -> None:
    """Test that PrunerOrchestrator handles database disposal failures."""
    pruner = PrunerOrchestrator(app=None)

    # Mock dispose_async_engine to raise exception
    with patch("application.mothership.db.engine.dispose_async_engine", side_effect=RuntimeError("Disposal failed")):
        with pytest.raises(RuntimeError, match="Disposal failed"):
            await pruner._dispose_database_engine([])


@pytest.mark.asyncio
async def test_pruner_records_metrics() -> None:
    """Test that PrunerOrchestrator records metrics for disposal."""
    pruner = PrunerOrchestrator(app=None)

    # Mock both dispose and profiler
    with patch("application.mothership.db.engine.dispose_async_engine", new_callable=AsyncMock):
        with patch("grid.security.parasite_guard._profiler") as mock_profiler:
            await pruner._dispose_database_engine([])

            # Verify success metric was recorded
            mock_profiler.record_db_engine_disposal_success.assert_called_once()


@pytest.mark.asyncio
async def test_pruner_records_failure_metrics() -> None:
    """Test that PrunerOrchestrator records failure metrics."""
    pruner = PrunerOrchestrator(app=None)

    # Mock dispose to raise exception
    with patch("application.mothership.db.engine.dispose_async_engine", side_effect=RuntimeError("Failed")):
        with patch("grid.security.parasite_guard._profiler") as mock_profiler:
            with pytest.raises(RuntimeError):
                await pruner._dispose_database_engine([])

            # Verify failure metric was recorded
            mock_profiler.record_db_engine_disposal_failure.assert_called_once()


@pytest.mark.asyncio
async def test_pruner_with_context_cleanup() -> None:
    """Test that PrunerOrchestrator cleans up context resources."""
    pruner = PrunerOrchestrator(app=None)

    # Create context with subscription
    subscription = MagicMock()
    context = ParasiteContext(
        id=uuid.uuid4(),
        rule="test_rule",
        subscription=subscription,
    )

    # Mock cleanup and disposal
    with patch.object(context, "cleanup", new_callable=AsyncMock) as mock_cleanup:
        with patch("application.mothership.db.engine.dispose_async_engine", new_callable=AsyncMock):
            with patch("grid.security.parasite_guard.ParasiteGuardConfig") as mock_config:
                mock_config.prune_enabled = True

                result = await pruner.prune(None, context=context)

                # Verify context cleanup was called
                mock_cleanup.assert_called_once()

                # Verify result includes context cleanup step
                assert any("Cleaned up resources" in step for step in result.steps)


@pytest.mark.asyncio
async def test_parasite_context_to_dict() -> None:
    """Test that ParasiteContext.to_dict() includes subscription info."""
    subscription = MagicMock()
    subscription.id = uuid.uuid4()

    context = ParasiteContext(
        id=uuid.uuid4(),
        rule="test_rule",
        subscription=subscription,
        cleanup_hooks=[lambda: None],
    )

    data = context.to_dict()

    # Verify subscription info is included
    assert data["has_subscription"] is True
    assert data["cleanup_hooks_count"] == 1
    assert "id" in data
    assert "rule" in data
    assert "status" in data
