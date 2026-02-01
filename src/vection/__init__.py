"""VECTION - Context Emergence Engine.

Velocity × Direction × Context = Cognitive Motion Intelligence

VECTION builds understanding over time rather than treating each request
as isolated. It discovers patterns across request streams, creates emergent
session context, and provides cognitive velocity tracking.

Core Modules:
- stream_context: Session/thread/anchor management
- emergence_layer: Pattern discovery without explicit rules
- velocity_tracker: Direction + momentum + drift tracking
- context_membrane: Retention/decay/salience scoring

The gap it fills: context_establishment should never be null.
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = [
    # Core classes
    "Vection",
    "StreamContext",
    "EmergenceLayer",
    "VelocityTracker",
    "ContextMembrane",
    # Schemas
    "VectionContext",
    "EmergenceSignal",
    "VelocityVector",
    "Anchor",
    # Protocols
    "Discoverable",
    "Projectable",
    # Functions
    "establish_context",
    "query_emergent",
    "project_context",
]

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass  # Future type-only imports go here

# Lazy imports to avoid circular dependencies
_Vection: Any = None
_StreamContext: Any = None
_EmergenceLayer: Any = None
_VelocityTracker: Any = None
_ContextMembrane: Any = None
_VectionContext: Any = None
_EmergenceSignal: Any = None
_VelocityVector: Any = None
_Anchor: Any = None


def __getattr__(name: str) -> Any:
    """Lazy import mechanism for VECTION components."""
    global _Vection, _StreamContext, _EmergenceLayer, _VelocityTracker
    global _ContextMembrane, _VectionContext, _EmergenceSignal, _VelocityVector, _Anchor

    if name == "Vection":
        if _Vection is None:
            from .core.engine import Vection as _Vection
        return _Vection

    if name == "StreamContext":
        if _StreamContext is None:
            from .core.stream_context import StreamContext as _StreamContext
        return _StreamContext

    if name == "EmergenceLayer":
        if _EmergenceLayer is None:
            from .core.emergence_layer import EmergenceLayer as _EmergenceLayer
        return _EmergenceLayer

    if name == "VelocityTracker":
        if _VelocityTracker is None:
            from .core.velocity_tracker import VelocityTracker as _VelocityTracker
        return _VelocityTracker

    if name == "ContextMembrane":
        if _ContextMembrane is None:
            from .core.context_membrane import ContextMembrane as _ContextMembrane
        return _ContextMembrane

    if name == "VectionContext":
        if _VectionContext is None:
            from .schemas.context_state import VectionContext as _VectionContext
        return _VectionContext

    if name == "EmergenceSignal":
        if _EmergenceSignal is None:
            from .schemas.emergence_signal import EmergenceSignal as _EmergenceSignal
        return _EmergenceSignal

    if name == "VelocityVector":
        if _VelocityVector is None:
            from .schemas.velocity_vector import VelocityVector as _VelocityVector
        return _VelocityVector

    if name == "Anchor":
        if _Anchor is None:
            from .schemas.context_state import Anchor as _Anchor
        return _Anchor

    if name == "Discoverable":
        from .protocols.discoverable import Discoverable

        return Discoverable

    if name == "Projectable":
        from .protocols.projectable import Projectable

        return Projectable

    if name in ("establish_context", "query_emergent", "project_context"):
        from .core.engine import Vection

        engine = Vection.get_instance()
        return getattr(engine, name.replace("_context", "").replace("_emergent", "_emergent"))

    raise AttributeError(f"module 'vection' has no attribute {name!r}")


# Singleton instance accessor
_instance: Any = None


def get_vection() -> Any:
    """Get the global VECTION instance.

    Returns:
        Vection: The singleton VECTION engine instance.
    """
    global _instance
    if _instance is None:
        from .core.engine import Vection

        _instance = Vection()
    return _instance


async def establish_context(session_id: str, event: Any) -> Any:
    """Establish context for a session.

    Args:
        session_id: Unique session identifier.
        event: The interaction event to process.

    Returns:
        VectionContext: The established context.
    """
    engine = get_vection()
    return await engine.establish(session_id, event)


async def query_emergent(session_id: str, query: str) -> Any:
    """Query emergent patterns for a session.

    Args:
        session_id: Unique session identifier.
        query: Query string for pattern matching.

    Returns:
        list[EmergenceSignal]: Relevant emergent signals.
    """
    engine = get_vection()
    return await engine.query_emergent(session_id, query)


async def project_context(session_id: str, steps: int = 3) -> Any:
    """Project future context needs.

    Args:
        session_id: Unique session identifier.
        steps: Number of steps to project forward.

    Returns:
        list[str]: Projected context needs.
    """
    engine = get_vection()
    return await engine.project(session_id, steps)
