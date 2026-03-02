"""Guardrail tool registry: maps tool names to callables."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from .policy import GuardrailPolicy
from .tools.access_control import access_control_tool
from .tools.audit import audit_tool
from .tools.auth import auth_tool
from .tools.base import GuardrailToolResult
from .tools.pii import pii_redact_tool
from .tools.rate_limit import rate_limit_tool
from .tools.result_filter import result_filter_tool
from .tools.sanitize import sanitize_tool

GuardrailToolFn = Callable[..., GuardrailToolResult | Awaitable[GuardrailToolResult]]


def create_default_registry(policy: GuardrailPolicy | None = None) -> GuardrailToolRegistry:
    """Create a registry with all built-in tools registered."""
    reg = GuardrailToolRegistry(policy or GuardrailPolicy.default())
    reg.register("auth", auth_tool)
    reg.register("rate_limit", rate_limit_tool)
    reg.register("sanitize", sanitize_tool)
    reg.register("access_control", access_control_tool)
    reg.register("pii_redact", pii_redact_tool)
    reg.register("result_filter", result_filter_tool)
    reg.register("audit", audit_tool)
    return reg


class GuardrailToolRegistry:
    """Registry of guardrail tools, driven by policy."""

    def __init__(self, policy: GuardrailPolicy | None = None) -> None:
        self.policy = policy or GuardrailPolicy.default()
        self._tools: dict[str, GuardrailToolFn] = {}

    def register(self, name: str, fn: GuardrailToolFn) -> None:
        """Register a tool by name."""
        self._tools[name] = fn

    def get(self, name: str) -> GuardrailToolFn | None:
        """Get a registered tool by name."""
        return self._tools.get(name)

    def get_parallel_group(self, phase: str) -> list[str]:
        """Return tool names to run in parallel for a phase."""
        return self.policy.get_parallel_group(phase)

    def get_tools_for_phase(self, phase: str) -> list[tuple[str, GuardrailToolFn]]:
        """Return (name, fn) pairs for tools in the phase, in registration order."""
        names = self.get_parallel_group(phase)
        return [(n, self._tools[n]) for n in names if n in self._tools]
