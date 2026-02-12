"""Pattern recognition package."""

from .embedded_agentic import EmbeddedAgenticDetector, ExtendedPatternRecognition
from .hybrid_detection import (
    HybridPatternDetector,
    HybridPatternResult,
    NeuralPatternDetector,
    PatternDetectionResult,
    StatisticalPatternDetector,
    SyntacticPatternDetector,
)
from .recognition import PatternRecognition

__all__ = [
    "PatternRecognition",
    "EmbeddedAgenticDetector",
    "ExtendedPatternRecognition",
    "StatisticalPatternDetector",
    "SyntacticPatternDetector",
    "NeuralPatternDetector",
    "HybridPatternDetector",
    "PatternDetectionResult",
    "HybridPatternResult",
]
