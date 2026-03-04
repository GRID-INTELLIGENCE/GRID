"""PII redaction guardrail tool: detects and redacts PII in search results."""

from __future__ import annotations

import re

from .base import GuardrailContext, GuardrailToolResult, ToolResult

# Base PII patterns (US-focused; extend as needed)
BASE_SSN_PATTERN = re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b")
BASE_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
BASE_PHONE_PATTERN = re.compile(r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

BASE_PII_PATTERNS = [
    ("SSN", BASE_SSN_PATTERN, "[SSN_REDACTED]"),
    ("EMAIL", BASE_EMAIL_PATTERN, "[EMAIL_REDACTED]"),
    ("PHONE", BASE_PHONE_PATTERN, "[PHONE_REDACTED]"),
]


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


def _redact_text(text: str, patterns: list[tuple[str, re.Pattern, str]]) -> str:
    """Redact PII from text using provided patterns."""
    out = text
    for _, pattern, replacement in patterns:
        out = pattern.sub(replacement, out)
    return out


def _redact_value(val: object, patterns: list[tuple[str, re.Pattern, str]]) -> object:
    if isinstance(val, str):
        return _redact_text(val, patterns)
    if isinstance(val, dict):
        return {k: _redact_value(v, patterns) for k, v in val.items()}
    if isinstance(val, list):
        return [_redact_value(v, patterns) for v in val]
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

    # Get patterns to use (profile-specific or base)
    # ReDoS mitigation: reject pattern strings > 500 chars (profile patterns from admin config)
    MAX_PROFILE_PATTERN_LENGTH = 500
    patterns_to_use = BASE_PII_PATTERNS
    if ctx.profile and hasattr(ctx.profile, "patterns") and "pii_redact" in ctx.profile.patterns:
        try:
            profile_patterns = []
            for pattern_str in ctx.profile.patterns["pii_redact"]:
                if not isinstance(pattern_str, str) or len(pattern_str) > MAX_PROFILE_PATTERN_LENGTH:
                    continue
                if "|" in pattern_str:
                    parts = pattern_str.split("|", 2)
                    if len(parts) == 3:
                        pattern_type, regex_str, replacement = parts
                        compiled_pattern = re.compile(regex_str)
                        profile_patterns.append((pattern_type, compiled_pattern, replacement))
                else:
                    compiled_pattern = re.compile(pattern_str)
                    profile_patterns.append(("CUSTOM", compiled_pattern, "[REDACTED]"))
            if profile_patterns:
                patterns_to_use = profile_patterns
        except (re.error, ValueError):
            patterns_to_use = BASE_PII_PATTERNS

    # Check budget limit
    budget_limit = 15000  # Default
    if ctx.profile and hasattr(ctx.profile, "budget_limits"):
        budget_limit = ctx.profile.budget_limits.get("pii_redact", 15000)

    total_chars = 0
    for hit in ctx.response.hits:
        if hasattr(hit, "document") and hit.document and hasattr(hit.document, "fields"):
            if isinstance(hit.document.fields, dict):
                for field_value in hit.document.fields.values():
                    if isinstance(field_value, str):
                        total_chars += len(field_value)

    if total_chars > budget_limit:
        message = _get_safety_validated_message(
            f"Content exceeds PII redaction budget limit ({budget_limit} characters)", "pii_redact", ctx
        )
        return GuardrailToolResult(
            tool_name="pii_redact",
            result=ToolResult.BLOCK,
            message=message,
        )

    # Apply redaction
    for hit in ctx.response.hits:
        if hasattr(hit, "document") and hit.document and hasattr(hit.document, "fields"):
            if isinstance(hit.document.fields, dict):
                hit.document.fields = {k: _redact_value(v, patterns_to_use) for k, v in hit.document.fields.items()}

    return GuardrailToolResult(
        tool_name="pii_redact",
        result=ToolResult.ALLOW,
    )
