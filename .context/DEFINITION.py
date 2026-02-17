"""
GRID Cognitive Intelligence (GCI) Framework - Core Definitions

This module defines the foundational elements of the GRID Cognitive Intelligence framework,
including the 9 cognition patterns, core data structures, and cognitive functions.

The framework models human-like cognitive processes including perception, attention,
pattern recognition, emotional tagging, and motor preparation with background factors
that influence cognitive performance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# =============================================================================
# COGNITION PATTERNS
# =============================================================================


class CognitionPattern:
    """
    The 9 fundamental cognition patterns in the GRID framework.

    These patterns represent the core cognitive processes that drive intelligent behavior:
    1. Flow - Continuous, optimal experience
    2. Spatial - Spatial relationships and navigation
    3. Rhythm - Temporal patterns and timing
    4. Color - Visual and conceptual differentiation
    5. Repetition - Learning through repetition
    6. Deviation - Anomaly detection
    7. Cause - Causal reasoning
    8. Time - Temporal awareness and planning
    9. Combination - Integrative thinking
    """

    FLOW = "flow"
    """Optimal experience pattern - state of deep focus and engagement."""

    SPATIAL = "spatial"
    """Spatial reasoning pattern - understanding relationships in space."""

    RHYTHM = "rhythm"
    """Temporal rhythm pattern - recognizing and predicting timing patterns."""

    COLOR = "color"
    """Conceptual differentiation pattern - distinguishing categories and types."""

    REPETITION = "repetition"
    """Learning through repetition pattern - habit formation and skill acquisition."""

    DEVIATION = "deviation"
    """Anomaly detection pattern - identifying unexpected changes or outliers."""

    CAUSE = "cause"
    """Causal reasoning pattern - understanding cause-effect relationships."""

    TIME = "time"
    """Temporal awareness pattern - planning and time management."""

    COMBINATION = "combination"
    """Integrative thinking pattern - combining concepts to form new ideas."""

    @classmethod
    def all_patterns(cls) -> list[str]:
        """Return all cognition patterns."""
        return [
            cls.FLOW,
            cls.SPATIAL,
            cls.RHYTHM,
            cls.COLOR,
            cls.REPETITION,
            cls.DEVIATION,
            cls.CAUSE,
            cls.TIME,
            cls.COMBINATION,
        ]

    @classmethod
    def get_relationships(cls) -> dict[str, list[str]]:
        """Get relationships between cognition patterns."""
        return {
            cls.FLOW: [cls.RHYTHM, cls.TIME],
            cls.SPATIAL: [cls.COLOR],
            cls.RHYTHM: [cls.FLOW, cls.TIME],
            cls.COLOR: [cls.SPATIAL, cls.DEVIATION],
            cls.REPETITION: [],
            cls.DEVIATION: [cls.COLOR, cls.CAUSE],
            cls.CAUSE: [cls.DEVIATION, cls.TIME],
            cls.TIME: [cls.FLOW, cls.RHYTHM, cls.CAUSE],
            cls.COMBINATION: cls.all_patterns(),
        }


# =============================================================================
# ENUMS
# =============================================================================


class CognitiveEvent(Enum):
    """Types of cognitive events that occur during processing."""

    PERCEPTION = "perception"
    """Initial sensory input processing."""

    ATTENTION_SHIFT = "attention_shift"
    """Change in focus of attention."""

    MEMORY_ACTIVATION = "memory_activation"
    """Retrieval of information from memory."""

    PATTERN_MATCH = "pattern_match"
    """Recognition of a known pattern."""

    EMOTIONAL_TAG = "emotional_tag"
    """Assignment of emotional valence to content."""

    MOTOR_PREPARATION = "motor_preparation"
    """Preparation for physical or virtual action."""

    INHIBITION = "inhibition"
    """Suppression of irrelevant information or responses."""

    INTEGRATION = "integration"
    """Combination of multiple cognitive processes."""


class BackgroundFactor(Enum):
    """Background factors that influence cognitive processing."""

    AROUSAL_LEVEL = "arousal_level"
    """Overall level of physiological and psychological activation."""

    COGNITIVE_LOAD = "cognitive_load"
    """Current mental effort being used in working memory."""

    PRIMING_STATE = "priming_state"
    """Recent exposure effects on current processing."""

    FATIGUE_ACCUMULATION = "fatigue_accumulation"
    """Accumulated mental fatigue affecting performance."""

    EXPECTATION_SET = "expectation_set"
    """Current set of expectations influencing perception."""

    MOOD_VALENCE = "mood_valence"
    """Overall emotional tone (positive-negative spectrum)."""

    HABIT_STRENGTH = "habit_strength"
    """Automaticity of current behavior patterns."""


class ActivityDomain(Enum):
    """Domains of human activity where cognition operates."""

    SOFTWARE_DEVELOPMENT = "software_development"
    """Writing, reviewing, and maintaining software code."""

    BUSINESS = "business"
    """Business operations, strategy, and decision-making."""

    DAILY_LIFE = "daily_life"
    """Everyday personal activities and routines."""

    CREATIVE_HOBBY = "creative_hobby"
    """Creative pursuits like art, music, or writing."""

    LEARNING = "learning"
    """Acquiring new knowledge or skills."""

    PHYSICAL_ACTIVITY = "physical_activity"
    """Sports, exercise, and physical tasks."""


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class CognitiveTrace:
    """
    A record of a cognitive event with contextual information.

    Represents a single cognitive operation including the event type,
    content, activation strength, and temporal information.
    """

    event: CognitiveEvent
    """The type of cognitive event."""

    timestamp: float
    """When the event occurred (Unix timestamp)."""

    content: dict[str, Any]
    """The content and details of the event."""

    activation_strength: float
    """Strength of the cognitive activation (0.0-1.0)."""

    decay_rate: float = 0.1
    """Rate at which activation decays over time (0.0-1.0)."""

    metadata: dict[str, Any] = field(default_factory=lambda: {})
    """Additional metadata about the event."""

    def get_current_activation(self, current_time: float) -> float:
        """Calculate current activation considering decay."""
        time_elapsed = current_time - self.timestamp
        return self.activation_strength * (1.0 - self.decay_rate) ** time_elapsed


@dataclass
class CognitiveState:
    """
    Current cognitive state including working memory, attention, and background factors.

    Models the complete cognitive context at a point in time, including:
    - Working memory contents
    - Attention focus
    - Background factors influencing processing
    - Recent cognitive traces
    """

    working_memory: list[Any] = field(default_factory=lambda: [])
    """Current contents of working memory (limited capacity)."""

    attention_focus: str = ""
    """Current object of attention."""

    background_factors: dict[BackgroundFactor, float] = field(default_factory=lambda: {})
    """Current levels of background factors (0.0-1.0)."""

    recent_traces: list[CognitiveTrace] = field(default_factory=lambda: [])
    """Recent cognitive events (limited to last 10)."""

    current_domain: ActivityDomain = ActivityDomain.SOFTWARE_DEVELOPMENT
    """Current activity domain."""

    def __post_init__(self):
        """Initialize default background factor values."""
        if not self.background_factors:
            for factor in BackgroundFactor:
                self.background_factors[factor] = 0.5  # Neutral default

    def add_trace(self, trace: CognitiveTrace) -> None:
        """Add a cognitive trace to recent history."""
        self.recent_traces.append(trace)
        # Limit to last 10 traces
        if len(self.recent_traces) > 10:
            self.recent_traces.pop(0)

    def get_factor(self, factor: BackgroundFactor) -> float:
        """Get the current value of a background factor."""
        return self.background_factors.get(factor, 0.5)

    def set_factor(self, factor: BackgroundFactor, value: float) -> None:
        """Set the value of a background factor (clamped to 0.0-1.0)."""
        self.background_factors[factor] = max(0.0, min(1.0, value))

    def is_overloaded(self) -> bool:
        """Check if cognitive load indicates overload."""
        return self.get_factor(BackgroundFactor.COGNITIVE_LOAD) > 0.8

    def is_in_flow(self) -> bool:
        """Check if current state indicates flow."""
        load = self.get_factor(BackgroundFactor.COGNITIVE_LOAD)
        arousal = self.get_factor(BackgroundFactor.AROUSAL_LEVEL)
        return 0.4 <= load <= 0.7 and 0.5 <= arousal <= 0.8


@dataclass
class Scenario:
    """
    A cognitive scenario representing a context for processing.

    Scenarios define the context in which cognitive operations occur,
    including active background factors, relevant patterns, and domain.
    """

    name: str
    """Name/description of the scenario."""

    domain: ActivityDomain
    """Domain of activity for this scenario."""

    active_factors: dict[BackgroundFactor, float] = field(default_factory=lambda: {})
    """Background factors active in this scenario."""

    relevant_patterns: list[str] = field(default_factory=lambda: [])
    """Cognition patterns relevant to this scenario."""

    expected_events: list[CognitiveEvent] = field(default_factory=lambda: [])
    """Expected cognitive events in this scenario."""

    def __post_init__(self):
        """Initialize default active factors."""
        if not self.active_factors:
            for factor in BackgroundFactor:
                self.active_factors[factor] = 0.5  # Neutral default

    def get_factor(self, factor: BackgroundFactor) -> float:
        """Get the value of an active factor."""
        return self.active_factors.get(factor, 0.5)

    def set_factor(self, factor: BackgroundFactor, value: float) -> None:
        """Set the value of an active factor (clamped to 0.0-1.0)."""
        self.active_factors[factor] = max(0.0, min(1.0, value))


@dataclass
class ContextReport:
    """
    A report on the current cognitive context with recommendations.

    Provides analysis of the current cognitive state and scenario,
    including performance predictions and task recommendations.
    """

    timestamp: float
    """When the report was generated."""

    domain: ActivityDomain
    """Current activity domain."""

    state_snapshot: dict[BackgroundFactor, float]
    """Snapshot of background factor values."""

    performance_prediction: float
    """Predicted performance level (0.0-1.0)."""

    risk_factors: list[str]
    """Identified risk factors affecting performance."""

    recommendations: list[str]
    """Recommendations for improving performance."""

    optimal_tasks: list[str]
    """Tasks well-suited to current cognitive state."""

    avoid_tasks: list[str]
    """Tasks poorly suited to current cognitive state."""

    role_in_development: str
    """Suggested role based on cognitive state."""


# =============================================================================
# CORE COGNITIVE FUNCTIONS
# =============================================================================


def perceive(stimulus: Any, state: CognitiveState) -> tuple[CognitiveTrace, CognitiveState]:
    """
    Process sensory input and create a perception event.

    Args:
        stimulus: The input to be perceived (text, image, event, etc.)
        state: Current cognitive state

    Returns:
        Tuple of (CognitiveTrace, updated CognitiveState)

    Cognitive Process:
        - Encodes raw stimulus into cognitive representation
        - Assesses complexity and novelty
        - Updates cognitive load based on processing effort
        - Creates perception trace with encoded content
    """
    # Create perception trace
    trace = CognitiveTrace(
        event=CognitiveEvent.PERCEPTION,
        timestamp=datetime.now().timestamp(),
        content={
            "raw": stimulus,
            "complexity": _assess_complexity(stimulus),
            "novelty": _assess_novelty(stimulus, state),
            "blind_spots_risk": state.is_overloaded(),
        },
        activation_strength=0.7,
    )

    # Update state
    new_state = _deep_copy_state(state)
    new_state.add_trace(trace)

    # Increase cognitive load based on complexity
    current_load = new_state.get_factor(BackgroundFactor.COGNITIVE_LOAD)
    complexity_factor = trace.content["complexity"]
    new_state.set_factor(BackgroundFactor.COGNITIVE_LOAD, min(1.0, current_load + (complexity_factor * 0.1)))

    return trace, new_state


def shift_attention(target: str, state: CognitiveState) -> tuple[CognitiveTrace, CognitiveState]:
    """
    Shift attention focus to a new target.

    Args:
        target: The new attention target
        state: Current cognitive state

    Returns:
        Tuple of (CognitiveTrace, updated CognitiveState)

    Cognitive Process:
        - Records current focus before shifting
        - Calculates context switch cost based on factors
        - Updates attention focus
        - Adjusts cognitive load and priming
    """
    # Create attention shift trace
    trace = CognitiveTrace(
        event=CognitiveEvent.ATTENTION_SHIFT,
        timestamp=datetime.now().timestamp(),
        content={
            "from": state.attention_focus,
            "to": target,
            "context_switch_cost": _calculate_switch_cost(state),
            "estimated_recovery_minutes": _estimate_recovery_time(state),
        },
        activation_strength=0.6,
    )

    # Update state
    new_state = _deep_copy_state(state)
    new_state.attention_focus = target
    new_state.add_trace(trace)

    # Increase cognitive load based on switch cost
    current_load = new_state.get_factor(BackgroundFactor.COGNITIVE_LOAD)
    switch_cost = trace.content["context_switch_cost"]
    new_state.set_factor(BackgroundFactor.COGNITIVE_LOAD, min(1.0, current_load + (switch_cost * 0.2)))

    # Reset priming after attention shift
    new_state.set_factor(BackgroundFactor.PRIMING_STATE, 0.0)

    return trace, new_state


def match_pattern(input_data: Any, pattern: str, state: CognitiveState) -> tuple[CognitiveTrace, CognitiveState]:
    """
    Match input data against a known pattern.

    Args:
        input_data: Data to match against pattern
        pattern: Pattern identifier or template
        state: Current cognitive state

    Returns:
        Tuple of (CognitiveTrace, updated CognitiveState)

    Cognitive Process:
        - Compares input to pattern template
        - Calculates match confidence
        - Assesses confirmation bias risk
        - Updates habit strength based on match
    """
    # Calculate match confidence
    confidence = _calculate_match_confidence(input_data, pattern, state)

    # Create pattern match trace
    trace = CognitiveTrace(
        event=CognitiveEvent.PATTERN_MATCH,
        timestamp=datetime.now().timestamp(),
        content={
            "input": input_data,
            "template": pattern,
            "match_confidence": confidence,
            "confirmation_bias_risk": state.get_factor(BackgroundFactor.EXPECTATION_SET) > 0.7,
        },
        activation_strength=confidence,
    )

    # Update state
    new_state = _deep_copy_state(state)
    new_state.add_trace(trace)

    # Strengthen habit based on successful match
    current_habit = new_state.get_factor(BackgroundFactor.HABIT_STRENGTH)
    new_state.set_factor(BackgroundFactor.HABIT_STRENGTH, min(1.0, current_habit + (confidence * 0.1)))

    return trace, new_state


def tag_emotion(
    content: str, valence: float, intensity: float, state: CognitiveState
) -> tuple[CognitiveTrace, CognitiveState]:
    """
    Assign emotional tags to content.

    Args:
        content: Content to be emotionally tagged
        valence: Emotional valence (-1.0 to 1.0, negative to positive)
        intensity: Emotional intensity (0.0-1.0)
        state: Current cognitive state

    Returns:
        Tuple of (CognitiveTrace, updated CognitiveState)

    Cognitive Process:
        - Modulates intensity based on mood congruence
        - Dampens intensity based on fatigue
        - Updates mood valence based on emotional content
        - Flags potential burnout risk
    """
    # Apply mood congruence effect
    mood = state.get_factor(BackgroundFactor.MOOD_VALENCE)
    mood_congruence = 1.0 + (mood * valence * 0.3)  # Amplify congruent emotions

    # Apply fatigue dampening
    fatigue = state.get_factor(BackgroundFactor.FATIGUE_ACCUMULATION)
    fatigue_dampening = 1.0 - (fatigue * 0.5)

    # Calculate final intensity
    final_intensity = min(1.0, max(0.0, intensity * mood_congruence * fatigue_dampening))

    # Create emotional tag trace
    trace = CognitiveTrace(
        event=CognitiveEvent.EMOTIONAL_TAG,
        timestamp=datetime.now().timestamp(),
        content={
            "content": content,
            "valence": valence,
            "original_intensity": intensity,
            "final_intensity": final_intensity,
            "mood_congruence_effect": mood_congruence,
            "fatigue_dampening": fatigue_dampening,
            "burnout_risk": fatigue > 0.8 and valence < -0.5,
        },
        activation_strength=final_intensity,
    )

    # Update state
    new_state = _deep_copy_state(state)
    new_state.add_trace(trace)

    # Update mood based on emotional content
    mood_shift = valence * final_intensity * 0.1
    new_mood = new_state.get_factor(BackgroundFactor.MOOD_VALENCE) + mood_shift
    new_state.set_factor(BackgroundFactor.MOOD_VALENCE, new_mood)

    return trace, new_state


def prepare_motor(action: str, state: CognitiveState) -> tuple[CognitiveTrace, CognitiveState]:
    """
    Prepare for motor action (physical or virtual).

    Args:
        action: The action to prepare for
        state: Current cognitive state

    Returns:
        Tuple of (CognitiveTrace, updated CognitiveState)

    Cognitive Process:
        - Calculates readiness based on habit, load, and arousal
        - Applies Yerkes-Dodson law (optimal arousal)
        - Flags if warmup is needed
        - Updates cognitive load
    """
    # Calculate readiness factors
    habit = state.get_factor(BackgroundFactor.HABIT_STRENGTH)
    load = state.get_factor(BackgroundFactor.COGNITIVE_LOAD)
    arousal = state.get_factor(BackgroundFactor.AROUSAL_LEVEL)

    # Apply Yerkes-Dodson law (inverted U-shaped curve)
    arousal_factor = 4 * arousal * (1 - arousal)  # Peaks at arousal = 0.5

    # Calculate readiness
    readiness = (habit * 0.4) + (arousal_factor * 0.4) - (load * 0.2)
    readiness = max(0.0, min(1.0, readiness))  # Clamp to [0, 1]

    # Create motor preparation trace
    trace = CognitiveTrace(
        event=CognitiveEvent.MOTOR_PREPARATION,
        timestamp=datetime.now().timestamp(),
        content={
            "action": action,
            "readiness": readiness,
            "habit_factor": habit,
            "arousal_factor": arousal_factor,
            "load_factor": load,
            "warmup_needed": readiness < 0.3,
        },
        activation_strength=readiness,
    )

    # Update state
    new_state = _deep_copy_state(state)
    new_state.add_trace(trace)

    # Increase cognitive load slightly
    new_load = min(1.0, load + 0.05)
    new_state.set_factor(BackgroundFactor.COGNITIVE_LOAD, new_load)

    return trace, new_state


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _deep_copy_state(state: CognitiveState) -> CognitiveState:
    """Create a deep copy of a CognitiveState."""
    return CognitiveState(
        working_memory=state.working_memory.copy(),
        attention_focus=state.attention_focus,
        background_factors=state.background_factors.copy(),
        recent_traces=state.recent_traces.copy(),
        current_domain=state.current_domain,
    )


def _assess_complexity(stimulus: Any) -> float:
    """Assess the complexity of a stimulus (0.0-1.0)."""
    if isinstance(stimulus, str):
        return min(1.0, len(stimulus) / 1000)  # Simple length-based complexity
    elif hasattr(stimulus, "__len__"):
        return min(1.0, len(stimulus) / 100)  # For lists, dicts, etc.
    return 0.5  # Default complexity


def _assess_novelty(stimulus: Any, state: CognitiveState) -> float:
    """Assess the novelty of a stimulus relative to current state (0.0-1.0)."""
    # Simple implementation - check if similar to recent working memory items
    if not state.working_memory:
        return 0.5

    similarity = 0.0
    for item in state.working_memory:
        if str(stimulus) == str(item):
            similarity += 1.0

    return 1.0 - (similarity / len(state.working_memory))


def _calculate_switch_cost(state: CognitiveState) -> float:
    """Calculate the cost of an attention switch (0.0-1.0)."""
    load = state.get_factor(BackgroundFactor.COGNITIVE_LOAD)
    priming = state.get_factor(BackgroundFactor.PRIMING_STATE)
    fatigue = state.get_factor(BackgroundFactor.FATIGUE_ACCUMULATION)

    # Higher load and fatigue increase switch cost
    # Higher priming reduces switch cost
    return min(1.0, max(0.0, (load * 0.5) + (fatigue * 0.3) - (priming * 0.4)))


def _estimate_recovery_time(state: CognitiveState) -> float:
    """Estimate recovery time from attention switch in minutes."""
    load = state.get_factor(BackgroundFactor.COGNITIVE_LOAD)
    fatigue = state.get_factor(BackgroundFactor.FATIGUE_ACCUMULATION)

    # Base recovery time plus load/fatigue effects
    return 0.5 + (load * 5) + (fatigue * 10)


def _calculate_match_confidence(input_data: Any, pattern: str, state: CognitiveState) -> float:
    """Calculate confidence in pattern match (0.0-1.0)."""
    # Simple implementation - check for pattern in input
    if isinstance(input_data, str) and pattern.lower() in input_data.lower():
        base_confidence = 0.8
    elif pattern in str(input_data):
        base_confidence = 0.6
    else:
        base_confidence = 0.2

    # Apply expectation bias
    expectation = state.get_factor(BackgroundFactor.EXPECTATION_SET)
    expectation_bias = 1.0 + (expectation * 0.3)  # Up to 30% boost

    return min(1.0, base_confidence * expectation_bias)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Cognition patterns
    "CognitionPattern",
    # Enums
    "CognitiveEvent",
    "BackgroundFactor",
    "ActivityDomain",
    # Data classes
    "CognitiveTrace",
    "CognitiveState",
    "Scenario",
    "ContextReport",
    # Core functions
    "perceive",
    "shift_attention",
    "match_pattern",
    "tag_emotion",
    "prepare_motor",
]
