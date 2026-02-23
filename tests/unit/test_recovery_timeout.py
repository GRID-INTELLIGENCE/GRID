"""Tests for RecoveryEngine per-attempt timeout functionality."""

import asyncio

import pytest

from grid.agentic.recovery_engine import RecoveryEngine


@pytest.mark.unit
class TestRecoveryTimeout:
    """Test suite for timeout_seconds parameter."""

    async def test_timeout_raises_timeout_error(self) -> None:
        """A slow task with timeout_seconds should raise TimeoutError."""

        async def slow_task() -> str:
            await asyncio.sleep(10.0)
            return "completed"

        engine = RecoveryEngine()
        with pytest.raises(TimeoutError):
            await engine.execute_with_recovery(
                slow_task,
                max_attempts=1,
                timeout_seconds=0.1,
            )

    async def test_timeout_on_first_attempt_with_max_attempts_one(self) -> None:
        """With max_attempts=1, timeout should cut off the slow task immediately."""

        async def slow_task() -> str:
            await asyncio.sleep(5.0)
            return "should not reach"

        engine = RecoveryEngine()
        with pytest.raises(TimeoutError):
            await engine.execute_with_recovery(
                slow_task,
                max_attempts=1,
                timeout_seconds=0.05,
            )

    async def test_no_timeout_when_task_completes_fast(self) -> None:
        """If task completes within timeout, no error should be raised."""

        async def fast_task() -> str:
            await asyncio.sleep(0.01)
            return "done"

        engine = RecoveryEngine()
        result = await engine.execute_with_recovery(
            fast_task,
            max_attempts=1,
            timeout_seconds=1.0,
        )
        assert result == "done"

    async def test_timeout_none_allows_slow_task(self) -> None:
        """When timeout_seconds is None, slow tasks should be allowed."""

        async def slow_task() -> str:
            await asyncio.sleep(0.1)
            return "completed"

        engine = RecoveryEngine()
        result = await engine.execute_with_recovery(
            slow_task,
            max_attempts=1,
            timeout_seconds=None,
        )
        assert result == "completed"
