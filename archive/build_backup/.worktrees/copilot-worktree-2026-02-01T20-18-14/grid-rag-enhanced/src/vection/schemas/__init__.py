"""VECTION Schemas - Core data structures for context emergence.

Defines the fundamental data types for:
- VelocityVector: Cognitive motion tracking
- EmergenceSignal: Discovered pattern signals
- VectionContext: Session context state
- Anchor: Thread anchoring points
"""

from __future__ import annotations

from .context_state import Anchor, VectionContext
from .emergence_signal import EmergenceSignal, SignalType
from .velocity_vector import VelocityVector

__all__ = [
    "VelocityVector",
    "EmergenceSignal",
    "SignalType",
    "VectionContext",
    "Anchor",
]
