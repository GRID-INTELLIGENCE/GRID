import asyncio
import time

import pytest

from grid.agentic.recovery_engine import RecoveryEngine


@pytest.mark.asyncio
async def test_execute_with_recovery_enforces_timeout() -> None:
    """Verify each recovery attempt respects timeout_seconds."""

    engine = RecoveryEngine()

    async def slow_task() -> str:
        await asyncio.sleep(1.0)
        return "success"

    start = time.perf_counter()

    with pytest.raises(asyncio.TimeoutError):
        await engine.execute_with_recovery(slow_task, max_attempts=1, timeout_seconds=0.1)

    elapsed = time.perf_counter() - start
    assert elapsed < 0.4
