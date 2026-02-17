"""Cognition Patterns module.

This module provides the 9 cognition patterns for GRID's cognitive architecture:
- Flow: Continuous motion/progression
- Spatial: Geometric relationships
- Rhythm: Temporal regularity
- Color: Multidimensional attributes
- Repetition: Reoccurring patterns
- Deviation: Unexpected changes
- Cause: Causal relationships
- Time: Temporal evolution
- Combination: Composite patterns
"""

from cognitive.patterns.explanations import (
    COMPOSITE_EXPLANATIONS,
    PATTERN_EXPLANATIONS,
    explain_resonance_with_patterns,
    format_explanation_for_user,
    generate_pattern_summary,
    get_all_explanations,
    get_composite_explanation,
    get_pattern_explanation,
    get_pattern_recommendations,
)
from cognitive.patterns.recognition import (
    CausePattern,
    ColorPattern,
    CombinationPattern,
    DeviationPattern,
    FlowPattern,
    PatternConfidence,
    PatternDetection,
    PatternFeatures,
    PatternMatcher,
    PatternRecognizer,
    RepetitionPattern,
    RhythmPattern,
    SpatialPattern,
    TimePattern,
    get_pattern_matcher,
)

__all__ = [
    # Patterns
    "FlowPattern",
    "SpatialPattern",
    "RhythmPattern",
    "ColorPattern",
    "RepetitionPattern",
    "DeviationPattern",
    "CausePattern",
    "TimePattern",
    "CombinationPattern",
    # Base classes
    "PatternRecognizer",
    "PatternDetection",
    "PatternFeatures",
    "PatternConfidence",
    # Orchestrator
    "PatternMatcher",
    "get_pattern_matcher",
    # Explanations
    "PATTERN_EXPLANATIONS",
    "COMPOSITE_EXPLANATIONS",
    "get_pattern_explanation",
    "get_all_explanations",
    "get_composite_explanation",
    "format_explanation_for_user",
    "get_pattern_recommendations",
    "generate_pattern_summary",
    "explain_resonance_with_patterns",
]
