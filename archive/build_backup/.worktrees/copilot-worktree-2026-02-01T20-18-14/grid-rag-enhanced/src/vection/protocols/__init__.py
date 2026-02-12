"""VECTION Protocols Package.

Defines protocol interfaces for VECTION components:
- Discoverable: Interface for entities that can be discovered through emergence
- Projectable: Interface for future projection capabilities

These protocols follow Python's structural subtyping approach,
enabling duck-typing with static type checking support.
"""

from __future__ import annotations

from .discoverable import (
    CorrelableDiscoverable,
    Discoverable,
    DiscoverableAdapter,
    SalientDiscoverable,
    is_discoverable,
    is_salient_discoverable,
    make_discoverable,
)
from .projectable import (
    DetailedProjectable,
    Projectable,
    ProjectionResult,
    ProjectionSource,
)

__all__ = [
    # Discoverable protocols
    "Discoverable",
    "SalientDiscoverable",
    "CorrelableDiscoverable",
    "DiscoverableAdapter",
    "is_discoverable",
    "is_salient_discoverable",
    "make_discoverable",
    # Projectable protocols
    "Projectable",
    "DetailedProjectable",
    "ProjectionSource",
    "ProjectionResult",
]
