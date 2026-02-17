"""VECTION Interfaces Package.

Provides integration bridges between VECTION and external systems:
- GridBridge: Integration with GRID cognitive engine
- ContextInterface: Public API for context operations

These interfaces enable VECTION to enhance existing cognitive systems
with emergent context and velocity tracking.
"""

from __future__ import annotations

__all__ = [
    "GridBridge",
    "ContextInterface",
    "VectionIntegration",
]

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .context_interface import ContextInterface
    from .grid_bridge import GridBridge, VectionIntegration


def __getattr__(name: str) -> Any:
    """Lazy import for interface components."""
    if name == "GridBridge":
        from .grid_bridge import GridBridge

        return GridBridge

    if name == "VectionIntegration":
        from .grid_bridge import VectionIntegration

        return VectionIntegration

    if name == "ContextInterface":
        from .context_interface import ContextInterface

        return ContextInterface

    raise AttributeError(f"module 'vection.interfaces' has no attribute {name!r}")
