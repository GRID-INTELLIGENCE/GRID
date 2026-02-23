from __future__ import annotations

import asyncio

import pytest

from grid.skills.base import SimpleSkill


def test_simple_skill_executes_async_handler_from_sync_context() -> None:
    """SimpleSkill.run should resolve coroutine handlers in sync call paths."""

    async def handler(args: dict[str, int]) -> dict[str, int]:
        await asyncio.sleep(0)
        return {"value": args["value"]}

    skill = SimpleSkill(id="test.async.sync", name="Test", description="test", handler=handler)
    result = skill.run({"value": 7})
    assert result == {"value": 7}


@pytest.mark.asyncio
async def test_simple_skill_executes_async_handler_with_running_loop() -> None:
    """SimpleSkill.run should also work when called inside an active event loop."""

    async def handler(args: dict[str, int]) -> dict[str, int]:
        await asyncio.sleep(0.01)
        return {"value": args["value"] * 2}

    skill = SimpleSkill(id="test.async.loop", name="Test", description="test", handler=handler)
    result = skill.run({"value": 5})
    assert result == {"value": 10}
