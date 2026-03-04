"""Base types for guardrail tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ToolResult(StrEnum):
    """Result of a guardrail tool evaluation."""

    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"


@dataclass
class GuardrailToolResult:
    """Result from a single guardrail tool."""

    tool_name: str
    result: ToolResult
    message: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)  # Pattern match details and metadata


@dataclass
class GuardrailContext:
    """Context passed to guardrail tools: request metadata and optional response."""

    request: Any  # RequestContext
    response: Any = None  # SearchResponse | None for pre_query phase
    config: Any = None  # SearchConfig for guardrail settings
    schema: Any = None  # IndexSchema | None for field-level checks
    profile: Any = None  # GuardrailProfile for persona-specific settings
    budget_tracker: dict[str, int] = field(default_factory=dict)  # Tool -> chars used
