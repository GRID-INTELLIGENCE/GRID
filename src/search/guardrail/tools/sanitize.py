"""Query sanitization guardrail tool: validates and sanitizes query input."""

from __future__ import annotations

import re

from .base import GuardrailContext, GuardrailToolResult, ToolResult

# Patterns that may indicate injection or manipulation attempts
DANGEROUS_PATTERNS = [
    re.compile(r"[,;{}\\]"),  # JSON/DSL-like syntax
    re.compile(r"(?i)(?:drop|delete|truncate|insert|update)\s+\w+"),
    re.compile(r"(?i)javascript\s*:"),
    re.compile(r"<script"),
    re.compile(r"\$\{|%\s*\{"),
]

MAX_QUERY_LENGTH = 10_000


def sanitize_tool(ctx: GuardrailContext) -> GuardrailToolResult:
    """Validate and sanitize query text. BLOCK on dangerous patterns or oversized input."""
    query = ctx.request.query_text if ctx.request else ""
    if not isinstance(query, str):
        return GuardrailToolResult(
            tool_name="sanitize",
            result=ToolResult.BLOCK,
            message="Query must be a string",
        )
    if len(query) > MAX_QUERY_LENGTH:
        return GuardrailToolResult(
            tool_name="sanitize",
            result=ToolResult.BLOCK,
            message=f"Query exceeds max length ({MAX_QUERY_LENGTH})",
        )
    for pat in DANGEROUS_PATTERNS:
        if pat.search(query):
            return GuardrailToolResult(
                tool_name="sanitize",
                result=ToolResult.BLOCK,
                message="Query contains disallowed patterns",
            )
    return GuardrailToolResult(
        tool_name="sanitize",
        result=ToolResult.ALLOW,
    )
