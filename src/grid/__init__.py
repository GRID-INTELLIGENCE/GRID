"""GRID Intelligence Layer - The Mind.

Core modules:
- essence: State representation and transformation
- patterns: Pattern recognition and emergence
- awareness: Context and observer mechanics
- evolution: Version management and natural growth
- interfaces: Bridges between layers
- tracing: Comprehensive source tracing and action origin tracking
- organization: Multi-org/multi-user management with discipline
- prompts: Custom user prompts context management
- quantum: Quantized architecture with locomotion
- senses: Extended cognitive sensory support (smell, touch, taste)
- processing: Periodic processing with emergency real-time flows
- entry_points: Optimized entry points for API, CLI, and services
"""

from typing import Any

try:
    from .essence.core_state import EssentialState
except ImportError:  # pragma: no cover
    EssentialState = None  # type: ignore

try:
    from .patterns.recognition import PatternRecognition
except ImportError:  # pragma: no cover
    PatternRecognition = None  # type: ignore

try:
    from .awareness.context import Context
except ImportError:  # pragma: no cover
    Context = None  # type: ignore

try:
    from .evolution.version import VersionState
except ImportError:  # pragma: no cover
    VersionState = None  # type: ignore

try:
    from .interfaces.bridge import QuantumBridge
except ImportError:  # pragma: no cover
    QuantumBridge = None  # type: ignore

# Initialize all to None before conditional imports
APIEntryPoint: Any = None
CLIEntryPoint: Any = None
ServiceEntryPoint: Any = None
DisciplineManager: Any = None
Organization: Any = None
OrganizationManager: Any = None
OrganizationRole: Any = None
User: Any = None
UserRole: Any = None
UserStatus: Any = None
EmergencyRealtimeProcessor: Any = None
PeriodicProcessor: Any = None
ProcessingMode: Any = None
RealtimeFlow: Any = None
Prompt: Any = None
PromptContext: Any = None
PromptManager: Any = None
PromptPriority: Any = None
PromptSource: Any = None
LocomotionEngine: Any = None
MovementDirection: Any = None
QuantizationLevel: Any = None
QuantizedState: Any = None
Quantizer: Any = None
QuantumEngine: Any = None
SensoryInput: Any = None
SensoryProcessor: Any = None
SensoryStore: Any = None
SensoryType: Any = None
ActionTrace: Any = None
TraceContext: Any = None
TraceManager: Any = None
TraceOrigin: Any = None
TraceStore: Any = None

try:  # pragma: no cover
    from .entry_points import APIEntryPoint, CLIEntryPoint, ServiceEntryPoint  # noqa: F401
except Exception:
    pass

try:  # pragma: no cover
    from .organization import (  # noqa: F401
        DisciplineManager,
        Organization,
        OrganizationManager,
        OrganizationRole,
        User,
        UserRole,
        UserStatus,
    )
except Exception:
    pass

try:  # pragma: no cover
    from .processing import EmergencyRealtimeProcessor, PeriodicProcessor, ProcessingMode, RealtimeFlow  # noqa: F401
except Exception:
    pass

try:  # pragma: no cover
    from .prompts import Prompt, PromptContext, PromptManager, PromptPriority, PromptSource  # noqa: F401
except Exception:
    pass

try:  # pragma: no cover
    from .quantum import (  # noqa: F401
        LocomotionEngine,
        MovementDirection,
        QuantizationLevel,
        QuantizedState,
        Quantizer,
        QuantumEngine,
    )
except Exception:
    pass

try:  # pragma: no cover
    from .senses import SensoryInput, SensoryProcessor, SensoryStore, SensoryType
except Exception:
    pass

try:  # pragma: no cover
    from .tracing import ActionTrace, TraceContext, TraceManager, TraceOrigin, TraceStore
except Exception:
    pass

# Environment sanitization startup hook
try:  # pragma: no cover
    from .security.environment import sanitize_environment

    # Sanitize environment on import
    _sanitization_report = sanitize_environment()

    # Optionally log the sanitization report
    if _sanitization_report and __name__ != "__main__":
        import logging

        logger = logging.getLogger(__name__)
        for category, messages in _sanitization_report.items():
            for message in messages:
                logger.debug(f"Environment Sanitization ({category}): {message}")
except ImportError:  # pragma: no cover
    # If environment sanitization fails, continue normally
    pass

__all__ = [
    # Core
    *(["EssentialState"] if EssentialState is not None else []),
    *(["PatternRecognition"] if PatternRecognition is not None else []),
    *(["Context"] if Context is not None else []),
    *(["VersionState"] if VersionState is not None else []),
    *(["QuantumBridge"] if QuantumBridge is not None else []),
    # Tracing
    *(["ActionTrace", "TraceContext", "TraceManager", "TraceOrigin", "TraceStore"] if ActionTrace is not None else []),
    # Organization
    *(
        [
            "Organization",
            "OrganizationRole",
            "OrganizationManager",
            "User",
            "UserRole",
            "UserStatus",
            "DisciplineManager",
        ]
        if Organization is not None
        else []
    ),
    # Prompts
    *(["Prompt", "PromptContext", "PromptManager", "PromptPriority", "PromptSource"] if Prompt is not None else []),
    # Quantum
    *(
        ["Quantizer", "QuantizationLevel", "QuantizedState", "LocomotionEngine", "MovementDirection", "QuantumEngine"]
        if Quantizer is not None
        else []
    ),
    # Senses
    *(["SensoryInput", "SensoryType", "SensoryProcessor", "SensoryStore"] if SensoryInput is not None else []),
    # Processing
    *(
        ["PeriodicProcessor", "ProcessingMode", "EmergencyRealtimeProcessor", "RealtimeFlow"]
        if PeriodicProcessor is not None
        else []
    ),
    # Entry Points
    *(["APIEntryPoint", "CLIEntryPoint", "ServiceEntryPoint"] if APIEntryPoint is not None else []),
]
