"""Query sanitization guardrail tool: validates and sanitizes query input."""

from __future__ import annotations

import re
from datetime import datetime

from .base import GuardrailContext, GuardrailToolResult, ToolResult

# Base dangerous patterns (fallback)
BASE_DANGEROUS_PATTERNS = [
    re.compile(r"[,;{}\\]"),  # JSON/DSL-like syntax
    re.compile(r"(?i)(?:drop|delete|truncate|insert|update)\s+\w+"),
    re.compile(r"(?i)javascript\s*:"),
    re.compile(r"<script"),
    re.compile(r"\$\{|%\s*\{"),
]

MAX_QUERY_LENGTH = 10_000


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


def sanitize_tool(ctx: GuardrailContext) -> GuardrailToolResult:
    """Validate and sanitize query text. BLOCK on dangerous patterns or oversized input."""
    query = ctx.request.query_text if ctx.request else ""
    if not isinstance(query, str):
        message = _get_safety_validated_message("Query must be a string", "sanitize", ctx)
        return GuardrailToolResult(
            tool_name="sanitize",
            result=ToolResult.BLOCK,
            message=message,
        )

    # Check budget limit
    budget_limit = 10000  # Default
    if ctx.config and hasattr(ctx.config, "policy") and ctx.config.policy:
        budget_limit = ctx.config.policy.get_budget_limit("sanitize")
    elif ctx.profile and hasattr(ctx.profile, "budget_limits"):
        budget_limit = ctx.profile.budget_limits.get("sanitize", 10000)

    if len(query) > budget_limit:
        message = _get_safety_validated_message(
            f"Query exceeds budget limit ({budget_limit} characters)", "sanitize", ctx
        )
        return GuardrailToolResult(
            tool_name="sanitize",
            result=ToolResult.BLOCK,
            message=message,
        )

    # Use profile-specific patterns if available
    # ReDoS mitigation: reject patterns > 500 chars (profile patterns from admin config)
    MAX_PROFILE_PATTERN_LENGTH = 500
    patterns_to_check = BASE_DANGEROUS_PATTERNS
    if ctx.profile and hasattr(ctx.profile, "patterns") and "sanitize" in ctx.profile.patterns:
        try:
            valid = [
                p
                for p in ctx.profile.patterns["sanitize"]
                if isinstance(p, str) and len(p) <= MAX_PROFILE_PATTERN_LENGTH
            ]
            patterns_to_check = [re.compile(p) for p in valid] if valid else BASE_DANGEROUS_PATTERNS
        except (re.error, TypeError):
            patterns_to_check = BASE_DANGEROUS_PATTERNS

    for pat in patterns_to_check:
        if pat.search(query):
            # Record provenance information
            provenance = {
                "pattern_type": "profile_specific"
                if ctx.profile and hasattr(ctx.profile, "patterns") and "sanitize" in ctx.profile.patterns
                else "base_fallback",
                "matched_pattern": pat.pattern,
                "query_length": len(query),
                "budget_limit": budget_limit,
                "profile_name": ctx.profile.name if ctx.profile else None,
                "timestamp": datetime.now().isoformat(),
            }

            message = _get_safety_validated_message("Query contains disallowed patterns", "sanitize", ctx)
            return GuardrailToolResult(
                tool_name="sanitize",
                result=ToolResult.BLOCK,
                message=message,
                provenance=provenance,
            )

    return GuardrailToolResult(
        tool_name="sanitize",
        result=ToolResult.ALLOW,
    )
