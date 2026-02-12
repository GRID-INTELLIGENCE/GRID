"""Cognitive Layer Module.

The GRID Cognitive Layer provides:
- Cognitive state tracking and management
- Load estimation and adaptation
- Processing mode detection (System 1/2)
- Mental model management
- 9 Cognition Patterns (Flow, Spatial, Rhythm, Color, Repetition, Deviation, Cause, Time, Combination)
- Dynamic XAI with cognitive context
- K1 prerequisites for geometric cognitive vectors

Main components:
- CognitiveEngine: Core orchestrator for all cognitive components
- ProfileStore: Persistent user profile storage and learning
- PatternMatcher: 9 pattern recognizers for cognitive analysis
- InteractionTracker: Track user interactions for cognitive inference
- ScaffoldingEngine: Dynamic content adaptation
- CognitiveRouter: Cognitive-aware request routing
"""

from cognitive.cognitive_engine import (
    Adaptation,
    CognitiveEngine,
    InteractionEvent,
    ScaffoldingAction,
    get_cognitive_engine,
)
from cognitive.interaction_tracker import (
    ActionType,
    InteractionSummary,
    InteractionTracker,
    Sentiment,
    get_interaction_tracker,
)
from cognitive.interaction_tracker import (
    InteractionEvent as TrackedEvent,
)
from cognitive.light_of_the_seven.cognitive_layer.schemas.cognitive_state import (
    CognitiveLoadType,
    CognitiveState,
    ProcessingMode,
)
from cognitive.light_of_the_seven.cognitive_layer.schemas.decision_context import (
    DecisionContext,
    DecisionType,
    DecisionUrgency,
)
from cognitive.light_of_the_seven.cognitive_layer.schemas.user_cognitive_profile import (
    DecisionStyle,
    ExpertiseLevel,
    LearningStyle,
    UserCognitiveProfile,
)
from cognitive.patterns import (
    CausePattern,
    ColorPattern,
    CombinationPattern,
    DeviationPattern,
    FlowPattern,
    PatternConfidence,
    PatternDetection,
    PatternMatcher,
    RepetitionPattern,
    RhythmPattern,
    SpatialPattern,
    TimePattern,
    explain_resonance_with_patterns,
    format_explanation_for_user,
    generate_pattern_summary,
    get_pattern_explanation,
    get_pattern_matcher,
)
from cognitive.profile_store import ProfileStore, get_profile_store
from cognitive.router import (
    Adaptation as RouterAdaptation,
)
from cognitive.router import (
    CognitiveRequestHandler,
    CognitiveRouter,
    Route,
    RouteType,
    get_cognitive_router,
)
from cognitive.scaffolding_engine import (
    ScaffoldingAction as ScaffoldAction,
)
from cognitive.scaffolding_engine import (
    ScaffoldingEngine,
    ScaffoldingResult,
    ScaffoldingStrategy,
    get_scaffolding_engine,
)

__all__ = [
    # Core Engine
    "CognitiveEngine",
    "get_cognitive_engine",
    "Adaptation",
    "InteractionEvent",
    "ScaffoldingAction",
    # Profile Management
    "ProfileStore",
    "get_profile_store",
    # Interaction Tracking
    "InteractionTracker",
    "get_interaction_tracker",
    "TrackedEvent",
    "InteractionSummary",
    "ActionType",
    "Sentiment",
    # Schemas
    "CognitiveState",
    "CognitiveLoadType",
    "ProcessingMode",
    "UserCognitiveProfile",
    "ExpertiseLevel",
    "LearningStyle",
    "DecisionStyle",
    "DecisionContext",
    "DecisionType",
    "DecisionUrgency",
    # Patterns
    "PatternMatcher",
    "get_pattern_matcher",
    "FlowPattern",
    "SpatialPattern",
    "RhythmPattern",
    "ColorPattern",
    "RepetitionPattern",
    "DeviationPattern",
    "CausePattern",
    "TimePattern",
    "CombinationPattern",
    "PatternDetection",
    "PatternConfidence",
    # Pattern Explanations
    "get_pattern_explanation",
    "format_explanation_for_user",
    "generate_pattern_summary",
    "explain_resonance_with_patterns",
    # Scaffolding
    "ScaffoldingEngine",
    "get_scaffolding_engine",
    "ScaffoldingResult",
    "ScaffoldingStrategy",
    "ScaffoldAction",
    # Router
    "CognitiveRouter",
    "get_cognitive_router",
    "Route",
    "RouteType",
    "RouterAdaptation",
    "CognitiveRequestHandler",
]
