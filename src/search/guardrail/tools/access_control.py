"""Access control guardrail tool: checks index/field permissions."""

from __future__ import annotations

from .base import GuardrailContext, GuardrailToolResult, ToolResult


def access_control_tool(ctx: GuardrailContext) -> GuardrailToolResult:
    """Check that the caller may access the requested index.

    Stub implementation: ALLOW. Can be extended with per-identity index allowlists.
    """
    index_name = ctx.request.index_name if ctx.request else ""
    identity = ctx.request.identity if ctx.request else None
    if not index_name:
        return GuardrailToolResult(
            tool_name="access_control",
            result=ToolResult.BLOCK,
            message="Index name required",
        )
    # Stub: allow all when identity present or when auth not enforced
    return GuardrailToolResult(
        tool_name="access_control",
        result=ToolResult.ALLOW,
        context={"index": index_name, "identity": identity},
    )
