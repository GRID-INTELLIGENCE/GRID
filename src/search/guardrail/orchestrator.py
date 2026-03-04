"""Guardrail orchestrator: runs policy-driven tools in parallel."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from .auth import AuthSignature
from .policy import GuardrailPolicy
from .registry import GuardrailToolRegistry, create_default_registry
from .tools.base import GuardrailContext, GuardrailToolResult, ToolResult

logger = logging.getLogger(__name__)


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

    def activate_profile(
        self,
        profile_name: str,
        user_id: str | None = None,
        auth_signature: AuthSignature | None = None,
        user_permissions: set[str] | None = None,
        user_role: str = "basic",
    ) -> bool:
        """Activate a persona profile with authentication and narrowed scope."""
        success = self.policy.activate_profile(
            profile_name=profile_name,
            user_id=user_id,
            auth_signature=auth_signature,
            user_permissions=user_permissions,
            user_role=user_role,
        )

        if success:
            # Update registry with new policy phases
            self.registry = create_default_registry(self.policy)

        return success

    async def run_pre_query(self, ctx: GuardrailContext) -> GuardrailResult:
        """Run pre-query tools in parallel. Block if any returns BLOCK."""
        ctx.config = self.config
        ctx.profile = self.policy.active_profile_obj
        ctx.budget_tracker = {}  # Reset budget tracker for new request

        # Pass policy reference for budget limit access
        if ctx.config:
            try:
                ctx.config.policy = self.policy
            except (AttributeError, TypeError, ValueError):
                logger.debug("Unable to attach policy onto config object %s", type(ctx.config).__name__)

        tools = self.registry.get_tools_for_phase("pre_query")
        if not tools:
            return GuardrailResult(blocked=False)

        # Check budget limits before execution
        for tool_name, _ in tools:
            budget_limit = self.policy.get_budget_limit(tool_name)
            if budget_limit > 0:
                ctx.budget_tracker[tool_name] = 0

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
        ctx.profile = self.policy.active_profile_obj

        # Pass policy reference for budget limit access
        if ctx.config:
            try:
                ctx.config.policy = self.policy
            except (AttributeError, TypeError, ValueError):
                logger.debug("Unable to attach policy onto config object %s", type(ctx.config).__name__)

        tools = self.registry.get_tools_for_phase("post_query")
        if not tools:
            return GuardrailResult(blocked=False)

        # Check budget limits for post-query tools
        for tool_name, _ in tools:
            budget_limit = self.policy.get_budget_limit(tool_name)
            if budget_limit > 0 and tool_name not in ctx.budget_tracker:
                ctx.budget_tracker[tool_name] = 0

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
