"""PII redaction guardrail tool: detects and redacts PII in search results."""

from __future__ import annotations

import re

from .base import GuardrailContext, GuardrailToolResult, ToolResult

# Simple PII patterns (US-focused; extend as needed)
SSN_PATTERN = re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")


def _redact_text(text: str) -> str:
    out = SSN_PATTERN.sub("[SSN_REDACTED]", text)
    out = EMAIL_PATTERN.sub("[EMAIL_REDACTED]", out)
    out = PHONE_PATTERN.sub("[PHONE_REDACTED]", out)
    return out


def _redact_value(val: object) -> object:
    if isinstance(val, str):
        return _redact_text(val)
    if isinstance(val, dict):
        return {k: _redact_value(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_redact_value(v) for v in val]
    return val


def pii_redact_tool(ctx: GuardrailContext) -> GuardrailToolResult:
    """Redact PII in search response documents. Modifies response in place."""
    config = ctx.config
    pii_redact = getattr(config, "guardrail_pii_redact", True) if config else True
    if not pii_redact or not ctx.response:
        return GuardrailToolResult(
            tool_name="pii_redact",
            result=ToolResult.ALLOW,
        )
    for hit in ctx.response.hits:
        if hasattr(hit, "document") and hit.document and hasattr(hit.document, "fields"):
            if isinstance(hit.document.fields, dict):
                hit.document.fields = {k: _redact_value(v) for k, v in hit.document.fields.items()}
    return GuardrailToolResult(
        tool_name="pii_redact",
        result=ToolResult.ALLOW,
    )
