"""
Activity Resonance Tool - Left-to-Right Communication System.

Provides fast, concise context from application/ (left) and vivid path
visualization from light_of_the_seven/ (right) with ADSR envelope feedback.
"""

from __future__ import annotations

# Graceful imports with fallbacks (Grid Core pattern)
try:
    from .activity_resonance import ActivityResonance, ResonanceState
except ImportError:  # pragma: no cover
    ActivityResonance = None  # type: ignore
    ResonanceState = None  # type: ignore

try:
    from .adsr_envelope import ADSREnvelope, EnvelopePhase
except ImportError:  # pragma: no cover
    ADSREnvelope = None  # type: ignore
    EnvelopePhase = None  # type: ignore

try:
    from .context_provider import ContextProvider
except ImportError:  # pragma: no cover
    ContextProvider = None  # type: ignore

try:
    from .path_visualizer import PathOption, PathVisualizer
except ImportError:  # pragma: no cover
    PathOption = None  # type: ignore
    PathVisualizer = None  # type: ignore

__all__ = [
    # Core components
    *(["ActivityResonance"] if ActivityResonance is not None else []),
    *(["ResonanceState"] if ResonanceState is not None else []),
    *(["ContextProvider"] if ContextProvider is not None else []),
    # Path visualization
    *(["PathVisualizer"] if PathVisualizer is not None else []),
    *(["PathOption"] if PathOption is not None else []),
    # ADSR envelope
    *(["ADSREnvelope"] if ADSREnvelope is not None else []),
    *(["EnvelopePhase"] if EnvelopePhase is not None else []),
]
