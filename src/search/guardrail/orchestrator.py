"""Guardrail orchestrator: runs policy-driven tools in parallel."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from .policy import GuardrailPolicy
from .registry import GuardrailToolRegistry, create_default_registry
from .tools.base import GuardrailContext, GuardrailToolResult, ToolResult


@dataclass
class GuardrailResult:
    """Result of pre-query guardrail run."""

    blocked: bool = False
    block_reason: str | None = None
    tool_results: list[GuardrailToolResult] = field(default_factory=list)


async def _run_tool(
    name: str,
    fn: Any,
    ctx: GuardrailContext,
) -> GuardrailToolResult:
    """Run a tool (sync or async) and return result."""
    result = fn(ctx)
    if asyncio.iscoroutine(result):
        return await result
    return result


class GuardrailOrchestrator:
    """Runs guardrail tools in parallel per policy phases."""

    def __init__(
        self,
        registry: GuardrailToolRegistry | None = None,
        config: Any = None,
        policy: GuardrailPolicy | None = None,
    ) -> None:
        self.policy = policy or GuardrailPolicy.default()
        self.registry = registry or create_default_registry(self.policy)
        self.config = config

    async def run_pre_query(self, ctx: GuardrailContext) -> GuardrailResult:
        """Run pre-query tools in parallel. Block if any returns BLOCK."""
        ctx.config = self.config
        tools = self.registry.get_tools_for_phase("pre_query")
        if not tools:
            return GuardrailResult(blocked=False)

        tasks = [_run_tool(name, fn, ctx) for name, fn in tools]
        results: list[GuardrailToolResult] = await asyncio.gather(*tasks)

        blocked = any(r.result == ToolResult.BLOCK for r in results)
        block_reason = None
        if blocked:
            blocking = next((r for r in results if r.result == ToolResult.BLOCK), None)
            block_reason = blocking.message if blocking else "Guardrail blocked"

        return GuardrailResult(
            blocked=blocked,
            block_reason=block_reason,
            tool_results=results,
        )

    async def run_post_query(
        self,
        ctx: GuardrailContext,
        response: Any,
    ) -> GuardrailResult:
        """Run post-query tools in parallel on the response."""
        ctx.config = self.config
        ctx.response = response
        tools = self.registry.get_tools_for_phase("post_query")
        if not tools:
            return GuardrailResult(blocked=False)

        tasks = [_run_tool(name, fn, ctx) for name, fn in tools]
        results: list[GuardrailToolResult] = await asyncio.gather(*tasks)

        blocked = any(r.result == ToolResult.BLOCK for r in results)
        block_reason = None
        if blocked:
            blocking = next((r for r in results if r.result == ToolResult.BLOCK), None)
            block_reason = blocking.message if blocking else "Post-query guardrail blocked"

        return GuardrailResult(
            blocked=blocked,
            block_reason=block_reason,
            tool_results=results,
        )
