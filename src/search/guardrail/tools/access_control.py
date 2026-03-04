"""Access control guardrail tool: checks index/field permissions."""

from __future__ import annotations

from .base import GuardrailContext, GuardrailToolResult, ToolResult


def access_control_tool(ctx: GuardrailContext) -> GuardrailToolResult:
    """Check that the caller may access the requested index and fields."""
    index_name = ctx.request.index_name if ctx.request else ""
    identity = ctx.request.identity if ctx.request else None
    profile = ctx.profile

    if not index_name:
        return GuardrailToolResult(
            tool_name="access_control",
            result=ToolResult.BLOCK,
            message="Index name required",
        )

    if profile:
        # 1. Check index allowlist
        if profile.allowed_indices and index_name not in profile.allowed_indices:
            return GuardrailToolResult(
                tool_name="access_control",
                result=ToolResult.BLOCK,
                message=f"Access to index '{index_name}' denied for profile '{profile.name}'",
            )

        # 2. Check field allowlist
        if index_name in profile.allowed_fields:
            allowed = set(profile.allowed_fields[index_name])

            # Check filter fields
            requested_filters = [f.field for f in ctx.request.filters] if ctx.request.filters else []
            for fld in requested_filters:
                if fld not in allowed:
                    return GuardrailToolResult(
                        tool_name="access_control",
                        result=ToolResult.BLOCK,
                        message=f"Filter field '{fld}' not allowed for index '{index_name}'",
                    )

            # Check facet fields
            requested_facets = ctx.request.facet_fields if ctx.request.facet_fields else []
            for fld in requested_facets:
                if fld not in allowed:
                    return GuardrailToolResult(
                        tool_name="access_control",
                        result=ToolResult.BLOCK,
                        message=f"Facet field '{fld}' not allowed for index '{index_name}'",
                    )

    return GuardrailToolResult(
        tool_name="access_control",
        result=ToolResult.ALLOW,
        context={"index": index_name, "identity": identity},
    )
