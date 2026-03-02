"""Auth guardrail tool: validates caller identity."""

from __future__ import annotations

from .base import GuardrailContext, GuardrailToolResult, ToolResult


def auth_tool(ctx: GuardrailContext) -> GuardrailToolResult:
    """Validate that the request has a valid identity.

    BLOCK if auth is required and identity is missing or invalid.
    """
    config = ctx.config
    auth_required = getattr(config, "guardrail_auth_required", True) if config else True
    identity = ctx.request.identity if ctx.request else None

    if auth_required and not identity:
        return GuardrailToolResult(
            tool_name="auth",
            result=ToolResult.BLOCK,
            message="Authentication required",
        )
    return GuardrailToolResult(
        tool_name="auth",
        result=ToolResult.ALLOW,
        context={"identity": identity} if identity else {},
    )
