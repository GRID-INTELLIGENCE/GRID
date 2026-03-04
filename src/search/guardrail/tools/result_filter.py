"""Result filter guardrail tool: redacts sensitive fields and caps result size."""

from __future__ import annotations

import re

from .base import GuardrailContext, GuardrailToolResult, ToolResult

REDACTED = "[REDACTED]"


def _get_safety_validated_message(message: str, tool_name: str, ctx: GuardrailContext) -> str:
    """Apply safety validation to tool messages."""
    if not ctx.profile:
        return message

    # Check perpetrator voice prevention
    perpetrator_patterns = [
        re.compile(r"\b(I|we|you)\b.*\b(kill|hurt|attack|damage)\b", re.IGNORECASE),
        re.compile(r"\b(I|we|you)\b.*\b(harm|threat|violence)\b", re.IGNORECASE),
    ]

    for pattern in perpetrator_patterns:
        if pattern.search(message):
            # Convert to descriptive noun form
            message = re.sub(
                r"\b(I|we|you)\b.*\b(kill|hurt|attack|damage|harm|threat|violence)\b",
                lambda m: "Homicide threat detected" if "kill" in m.group(0).lower() else "Threat pattern detected",
                message,
                flags=re.IGNORECASE,
            )

    # Add LIMITATIONS header if required
    if ctx.profile and ctx.profile.safety_rules.get("limitations_header", False):
        message = f"LIMITATIONS: Pattern-based detection is not sufficient for production safety without classifier context. {message}"

    return message


def result_filter_tool(ctx: GuardrailContext) -> GuardrailToolResult:
    """Redact sensitive fields from documents and enforce result size cap."""
    if not ctx.response:
        return GuardrailToolResult(
            tool_name="result_filter",
            result=ToolResult.ALLOW,
        )

    config = ctx.config
    max_size = getattr(config, "max_page_size", 1000) if config else 1000

    # Check budget limit for result processing
    budget_limit = 10000  # Default
    if ctx.profile and hasattr(ctx.profile, "budget_limits"):
        budget_limit = ctx.profile.budget_limits.get("result_filter", 10000)

    total_chars = 0
    for hit in ctx.response.hits:
        if hasattr(hit, "document") and hit.document and hasattr(hit.document, "fields"):
            if isinstance(hit.document.fields, dict):
                for field_value in hit.document.fields.values():
                    if isinstance(field_value, str):
                        total_chars += len(field_value)

    if total_chars > budget_limit:
        message = _get_safety_validated_message(
            f"Result content exceeds filter budget limit ({budget_limit} characters)", "result_filter", ctx
        )
        return GuardrailToolResult(
            tool_name="result_filter",
            result=ToolResult.BLOCK,
            message=message,
        )

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
