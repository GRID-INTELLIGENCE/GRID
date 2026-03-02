"""Result filter guardrail tool: redacts sensitive fields and caps result size."""

from __future__ import annotations

from .base import GuardrailContext, GuardrailToolResult, ToolResult

REDACTED = "[REDACTED]"


def result_filter_tool(ctx: GuardrailContext) -> GuardrailToolResult:
    """Redact sensitive fields from documents and enforce result size cap."""
    if not ctx.response:
        return GuardrailToolResult(
            tool_name="result_filter",
            result=ToolResult.ALLOW,
        )
    config = ctx.config
    max_size = getattr(config, "max_page_size", 1000) if config else 1000

    # Cap hits
    if len(ctx.response.hits) > max_size:
        ctx.response.hits = ctx.response.hits[:max_size]

    # Redact sensitive fields if schema available
    schema = ctx.schema
    if schema and hasattr(schema, "fields"):
        sensitive_fields = {k for k, v in schema.fields.items() if getattr(v, "sensitive", False)}
        if sensitive_fields:
            for hit in ctx.response.hits:
                if hasattr(hit, "document") and hit.document and hasattr(hit.document, "fields"):
                    if isinstance(hit.document.fields, dict):
                        for f in sensitive_fields:
                            if f in hit.document.fields:
                                hit.document.fields[f] = REDACTED

    return GuardrailToolResult(
        tool_name="result_filter",
        result=ToolResult.ALLOW,
    )
