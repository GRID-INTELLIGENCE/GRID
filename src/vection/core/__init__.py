"""VECTION Core - Context Emergence Engine core components.

The core module provides the primary orchestration for VECTION:
- Vection: Main engine orchestrator
- StreamContext: Session/thread/anchor management
- EmergenceLayer: Pattern discovery without explicit rules
- VelocityTracker: Direction + momentum + drift tracking
- ContextMembrane: Retention/decay/salience scoring

Usage:
    from vection.core import Vection

    engine = Vection()
    context = await engine.establish(session_id, event)
    signals = await engine.query_emergent(session_id, "pattern")
    projections = await engine.project(session_id, steps=3)
"""

from __future__ import annotations

__all__ = [
    "Vection",
    "StreamContext",
    "EmergenceLayer",
    "VelocityTracker",
    "ContextMembrane",
]

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .context_membrane import ContextMembrane
    from .emergence_layer import EmergenceLayer
    from .engine import Vection
    from .stream_context import StreamContext
    from .velocity_tracker import VelocityTracker


def __getattr__(name: str) -> Any:
    """Lazy import for core components."""
    if name == "Vection":
        from .engine import Vection

        return Vection

    if name == "StreamContext":
        from .stream_context import StreamContext

        return StreamContext

    if name == "EmergenceLayer":
        from .emergence_layer import EmergenceLayer

        return EmergenceLayer

    if name == "VelocityTracker":
        from .velocity_tracker import VelocityTracker

        return VelocityTracker

    if name == "ContextMembrane":
        from .context_membrane import ContextMembrane

        return ContextMembrane

    raise AttributeError(f"module 'vection.core' has no attribute {name!r}")
