"""
Cognition Module

This module provides a structured framework for cognitive intelligence modeling,
building on the foundational definitions from the Grid's Cognitive Intelligence (GCI) framework.
The module is organized into three core submodules:

- Flow: Manages cognitive event flows and state transitions
- Pattern: Handles pattern recognition and matching algorithms
- Time: Provides temporal context and timing mechanisms

The architecture is designed with extensibility in mind, allowing for advanced
features to be added while maintaining clean separation of concerns.
"""

from .Flow import CognitiveFlow, FlowManager
from .Pattern import CognitivePattern, PatternManager, PatternMatcher
from .Time import TemporalContext, TimeManager

__version__ = "1.0.0"
__all__ = [
    # Core managers
    "FlowManager",
    "PatternManager",
    "PatternMatcher",
    "TimeManager",
    # Core types
    "CognitiveFlow",
    "CognitivePattern",
    "TemporalContext",
]

# Import base definitions from GRID's cognitive framework
try:
    import os
    import sys

    # Add the .context directory to the path using absolute path relative to this module
    _module_dir = os.path.dirname(os.path.abspath(__file__))
    _grid_root = os.path.dirname(_module_dir)  # Go up from cognition/ to grid/
    context_path = os.path.join(_grid_root, ".context")
    if context_path not in sys.path:
        sys.path.insert(0, context_path)
    from DEFINITION import (  # type: ignore
        ActivityDomain,
        BackgroundFactor,
        CognitiveEvent,
        CognitiveState,
        CognitiveTrace,
        ContextReport,
        Scenario,
        match_pattern,
        # Core functions
        perceive,
        prepare_motor,
        shift_attention,
        tag_emotion,
    )
except ImportError:
    # Fallback for standalone usage
    import warnings

    warnings.warn("GRID cognitive definitions not available. Using fallback definitions.", stacklevel=2)

    # Minimal fallback definitions
    class CognitiveEvent:
        PERCEPTION = "perception"
        ATTENTION_SHIFT = "attention_shift"
        MEMORY_ACTIVATION = "memory_activation"
        PATTERN_MATCH = "pattern_match"
        EMOTIONAL_TAG = "emotional_tag"
        MOTOR_PREPARATION = "motor_preparation"
        INHIBITION = "inhibition"
        INTEGRATION = "integration"

    class BackgroundFactor:
        AROUSAL_LEVEL = "arousal_level"
        COGNITIVE_LOAD = "cognitive_load"
        PRIMING_STATE = "priming_state"
        FATIGUE_ACCUMULATION = "fatigue_accumulation"
        EXPECTATION_SET = "expectation_set"
        MOOD_VALENCE = "mood_valence"
        HABIT_STRENGTH = "habit_strength"

    class ActivityDomain:
        SOFTWARE_DEVELOPMENT = "software_development"
        BUSINESS = "business"
        DAILY_LIFE = "daily_life"
        CREATIVE_HOBBY = "creative_hobby"
        LEARNING = "learning"
        PHYSICAL_ACTIVITY = "physical_activity"

    # Placeholder classes for full compatibility
    CognitiveTrace = None
    Scenario = None
    CognitiveState = None
    ContextReport = None

    def perceive(*args, **kwargs):
        raise NotImplementedError("GRID perceive function not available")

    def shift_attention(*args, **kwargs):
        raise NotImplementedError("GRID shift_attention function not available")

    def match_pattern(*args, **kwargs):
        raise NotImplementedError("GRID match_pattern function not available")

    def tag_emotion(*args, **kwargs):
        raise NotImplementedError("GRID tag_emotion function not available")

    def prepare_motor(*args, **kwargs):
        raise NotImplementedError("GRID prepare_motor function not available")
