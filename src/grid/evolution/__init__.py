"""Evolution package for version management, Fibonacci evolution, landscape detection, and real-time adaptation."""

from .fibonacci_evolution import (
    FibonacciEvolutionEngine,
    FibonacciEvolutionState,
    FibonacciSequence,
)
from .landscape_detector import (
    LandscapeDetector,
    LandscapeShift,
    LandscapeSnapshot,
    NeuralLandscapeAnalyzer,
    StatisticalLandscapeAnalyzer,
    SyntacticLandscapeAnalyzer,
)
from .realtime_adapter import (
    AdaptationState,
    DynamicWeightNetwork,
    RealTimeAdapter,
    WeightUpdate,
)
from .version import VersionState

__all__ = [
    "VersionState",
    "FibonacciSequence",
    "FibonacciEvolutionEngine",
    "FibonacciEvolutionState",
    "LandscapeDetector",
    "LandscapeShift",
    "LandscapeSnapshot",
    "StatisticalLandscapeAnalyzer",
    "SyntacticLandscapeAnalyzer",
    "NeuralLandscapeAnalyzer",
    "RealTimeAdapter",
    "DynamicWeightNetwork",
    "AdaptationState",
    "WeightUpdate",
]
