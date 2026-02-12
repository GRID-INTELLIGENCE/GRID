"""Grid Services Package

This module provides lazy imports for service classes to avoid import-time
failures when optional dependencies (like mistralai) are not installed.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .mistral_agent import MistralAgentService

__all__ = ["MistralAgentService", "get_mistral_agent"]

# Lazy imports to avoid import-time failures when optional deps are missing
_MistralAgentService = None
_get_mistral_agent = None


def __getattr__(name: str):
    """Lazy import mechanism for services."""
    global _MistralAgentService, _get_mistral_agent

    if name == "MistralAgentService":
        if _MistralAgentService is None:
            from .mistral_agent import MistralAgentService as _MistralAgentService
        return _MistralAgentService

    if name == "get_mistral_agent":
        if _get_mistral_agent is None:
            from .mistral_agent import get_mistral_agent as _get_mistral_agent
        return _get_mistral_agent

    raise AttributeError(f"module 'grid.services' has no attribute {name!r}")
