"""VECTION Workers Package - Background discovery workers.

Non-blocking workers that operate in parallel to discover patterns,
correlations, and projections from request streams.

Workers:
- Correlator: Finds cross-request correlations
- Clusterer: Groups similar requests into clusters
- Projector: Projects future context needs

These workers enable VECTION's parallel discovery capability -
context emergence happens in the background without blocking requests.
"""

from __future__ import annotations

__all__ = [
    "Correlator",
    "Clusterer",
    "Projector",
    "WorkerPool",
    "WorkerStatus",
]

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .clusterer import Clusterer
    from .correlator import Correlator
    from .projector import Projector

# Lazy imports to avoid circular dependencies
_Correlator: Any = None
_Clusterer: Any = None
_Projector: Any = None


def __getattr__(name: str) -> Any:
    """Lazy import mechanism for worker components."""
    global _Correlator, _Clusterer, _Projector

    if name == "Correlator":
        if _Correlator is None:
            from .correlator import Correlator as _Correlator
        return _Correlator

    if name == "Clusterer":
        if _Clusterer is None:
            from .clusterer import Clusterer as _Clusterer
        return _Clusterer

    if name == "Projector":
        if _Projector is None:
            from .projector import Projector as _Projector
        return _Projector

    if name == "WorkerPool":
        from .pool import WorkerPool

        return WorkerPool

    if name == "WorkerStatus":
        from .base import WorkerStatus

        return WorkerStatus

    raise AttributeError(f"module 'vection.workers' has no attribute {name!r}")
