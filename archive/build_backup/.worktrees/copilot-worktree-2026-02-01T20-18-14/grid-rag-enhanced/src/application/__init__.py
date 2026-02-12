"""
GRID Application Layer.

FastAPI applications and services for the GRID system.
"""

from __future__ import annotations

# Graceful imports with fallbacks (Grid Core pattern)
try:
    from .mothership import (
        CockpitService,
        MothershipSettings,
        create_app,
        get_settings,
    )
except ImportError:  # pragma: no cover
    CockpitService = None  # type: ignore
    MothershipSettings = None  # type: ignore
    create_app = None  # type: ignore
    get_settings = None  # type: ignore

try:
    from .resonance import (
        ActivityResonance,
        ADSREnvelope,
        ContextProvider,
        PathVisualizer,
        ResonanceState,
    )
except ImportError:  # pragma: no cover
    ActivityResonance = None  # type: ignore
    ADSREnvelope = None  # type: ignore
    ContextProvider = None  # type: ignore
    PathVisualizer = None  # type: ignore
    ResonanceState = None  # type: ignore

__all__ = [
    # Mothership Application
    *(["CockpitService", "MothershipSettings", "create_app", "get_settings"] if create_app is not None else []),
    # Resonance Application
    *(
        [
            "ActivityResonance",
            "ADSREnvelope",
            "ContextProvider",
            "PathVisualizer",
            "ResonanceState",
        ]
        if ActivityResonance is not None
        else []
    ),
]
