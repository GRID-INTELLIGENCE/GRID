"""
Unit tests for Grid's Cognitive Intelligence (GCI) DEFINITION module.

Tests cover the core cognitive functions:
- perceive
- shift_attention
- match_pattern
- tag_emotion
- prepare_motor

NOTE: This test module is skipped until the full DEFINITION module is implemented.
The DEFINITION module at src/cognitive/context/DEFINITION.py currently only contains
ActivityDomain enum. The full cognitive framework with CognitiveState, CognitiveTrace,
perceive(), shift_attention(), match_pattern(), tag_emotion(), and prepare_motor()
needs to be implemented.
"""

from __future__ import annotations

import pytest

# Skip entire module until DEFINITION module is fully implemented
pytestmark = pytest.mark.skip(
    reason="DEFINITION module not fully implemented. "
    "See src/cognitive/context/DEFINITION.py - needs CognitiveState, CognitiveTrace, "
    "BackgroundFactor, perceive(), shift_attention(), match_pattern(), tag_emotion(), prepare_motor()"
)

# DEFINITION module is located in src/cognitive/context/ and added to sys.path by conftest.py
# The import cannot be resolved statically but works at runtime
try:
    from DEFINITION import (  # pyright: ignore[reportMissingImports]
        ActivityDomain,
        BackgroundFactor,
        CognitiveEvent,
        CognitiveState,
        CognitiveTrace,
        ContextReport,
        Scenario,
        match_pattern,
        perceive,
        prepare_motor,
        shift_attention,
        tag_emotion,
    )
except ImportError:
    # Provide stub types so the module can at least be parsed
    ActivityDomain = None
    BackgroundFactor = None
    CognitiveEvent = None
    CognitiveState = None
    CognitiveTrace = None
    ContextReport = None
    Scenario = None
    match_pattern = None
    perceive = None
    prepare_motor = None
    shift_attention = None
    tag_emotion = None

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def default_state() -> CognitiveState:
    """Create a default cognitive state with baseline factors."""
    return CognitiveState()


@pytest.fixture
def high_load_state() -> CognitiveState:
    """Create a cognitive state with high cognitive load."""
    state = CognitiveState()
    state.background_factors[BackgroundFactor.COGNITIVE_LOAD] = 0.9
    return state


@pytest.fixture
def fatigued_state() -> CognitiveState:
    """Create a cognitive state with high fatigue."""
    state = CognitiveState()
    state.background_factors[BackgroundFactor.FATIGUE_ACCUMULATION] = 0.8
    return state


@pytest.fixture
def primed_state() -> CognitiveState:
    """Create a cognitive state with high priming."""
    state = CognitiveState()
    state.background_factors[BackgroundFactor.PRIMING_STATE] = 0.9
    return state


# =============================================================================
# DATA STRUCTURE TESTS
# =============================================================================


class TestDataStructures:
    """Tests for GCI data structures."""

    def test_cognitive_state_default_factors(self, default_state: CognitiveState) -> None:
        """Default state should have all background factors at 0.5."""
        for factor in BackgroundFactor:
            assert factor in default_state.background_factors
            assert default_state.background_factors[factor] == 0.5

    def test_cognitive_state_working_memory_limit(self, default_state: CognitiveState) -> None:
        """Working memory should be limited to 7 items (Miller's Law)."""
        for i in range(10):
            default_state.working_memory.append(f"item_{i}")
        assert len(default_state.working_memory) == 7

    def test_cognitive_trace_creation(self) -> None:
        """CognitiveTrace should store event data correctly."""
        trace = CognitiveTrace(
            event=CognitiveEvent.PERCEPTION,
            timestamp=1234567890.0,
            content={"test": "data"},
            activation_strength=0.8,
        )
        assert trace.event == CognitiveEvent.PERCEPTION
        assert trace.timestamp == 1234567890.0
        assert trace.content == {"test": "data"}
        assert trace.activation_strength == 0.8
        assert trace.decay_rate == 0.1  # default

    def test_scenario_default_factors(self) -> None:
        """Scenario should initialize with default active factors."""
        scenario = Scenario(name="test", domain=ActivityDomain.SOFTWARE_DEVELOPMENT)
        assert BackgroundFactor.AROUSAL_LEVEL in scenario.active_factors
        assert scenario.active_factors[BackgroundFactor.AROUSAL_LEVEL] == 0.5

    def test_context_report_fields(self) -> None:
        """ContextReport should hold all required fields."""
        report = ContextReport(
            timestamp=1234567890.0,
            domain=ActivityDomain.SOFTWARE_DEVELOPMENT,
            state_snapshot={BackgroundFactor.AROUSAL_LEVEL: 0.6},
            performance_prediction=0.75,
            risk_factors=["fatigue"],
            recommendations=["take a break"],
            optimal_tasks=["code review"],
            avoid_tasks=["architecture decisions"],
            role_in_development="cognitive_monitor",
        )
        assert report.performance_prediction == 0.75
        assert "fatigue" in report.risk_factors


# =============================================================================
# PERCEIVE FUNCTION TESTS
# =============================================================================


class TestPerceive:
    """Tests for the perceive cognitive function."""

    def test_perceive_returns_trace_and_state(self, default_state: CognitiveState) -> None:
        """Perceive should return a tuple of (CognitiveTrace, CognitiveState)."""
        trace, new_state = perceive("test_stimulus", default_state)
        assert isinstance(trace, CognitiveTrace)
        assert isinstance(new_state, CognitiveState)

    def test_perceive_event_type(self, default_state: CognitiveState) -> None:
        """Perceive should create a PERCEPTION event."""
        trace, _ = perceive("test_stimulus", default_state)
        assert trace.event == CognitiveEvent.PERCEPTION

    def test_perceive_stores_raw_stimulus(self, default_state: CognitiveState) -> None:
        """Perceive should store the raw stimulus in content."""
        trace, _ = perceive("code_review_diff", default_state)
        assert trace.content["raw"] == "code_review_diff"

    def test_perceive_high_load_creates_blind_spots(self, high_load_state: CognitiveState) -> None:
        """High cognitive load should create blind spot risk."""
        trace, _ = perceive("complex_code", high_load_state)
        assert trace.content["blind_spots_risk"] is True

    def test_perceive_increases_cognitive_load(self, default_state: CognitiveState) -> None:
        """Perceiving should slightly increase cognitive load."""
        initial_load = default_state.background_factors[BackgroundFactor.COGNITIVE_LOAD]
        _, new_state = perceive("stimulus", default_state)
        new_load = new_state.background_factors[BackgroundFactor.COGNITIVE_LOAD]
        assert new_load > initial_load

    def test_perceive_adds_trace_to_history(self, default_state: CognitiveState) -> None:
        """Perceive should add the trace to recent_traces."""
        trace, new_state = perceive("stimulus", default_state)
        assert trace in new_state.recent_traces


# =============================================================================
# SHIFT_ATTENTION FUNCTION TESTS
# =============================================================================


class TestShiftAttention:
    """Tests for the shift_attention cognitive function."""

    def test_shift_attention_returns_trace_and_state(self, default_state: CognitiveState) -> None:
        """Shift attention should return a tuple of (CognitiveTrace, CognitiveState)."""
        trace, new_state = shift_attention("new_task", default_state)
        assert isinstance(trace, CognitiveTrace)
        assert isinstance(new_state, CognitiveState)

    def test_shift_attention_event_type(self, default_state: CognitiveState) -> None:
        """Shift attention should create an ATTENTION_SHIFT event."""
        trace, _ = shift_attention("new_task", default_state)
        assert trace.event == CognitiveEvent.ATTENTION_SHIFT

    def test_shift_attention_updates_focus(self, default_state: CognitiveState) -> None:
        """Shift attention should update attention_focus to the new target."""
        _, new_state = shift_attention("feature_branch", default_state)
        assert new_state.attention_focus == "feature_branch"

    def test_shift_attention_records_source_and_target(self, default_state: CognitiveState) -> None:
        """Shift attention should record both source and target."""
        default_state.attention_focus = "old_task"
        trace, _ = shift_attention("new_task", default_state)
        assert trace.content["from"] == "old_task"
        assert trace.content["to"] == "new_task"

    def test_shift_attention_high_load_increases_recovery_time(
        self, default_state: CognitiveState, high_load_state: CognitiveState
    ) -> None:
        """Higher cognitive load should increase recovery time estimate."""
        trace_normal, _ = shift_attention("task", default_state)
        trace_high_load, _ = shift_attention("task", high_load_state)
        assert (
            trace_high_load.content["estimated_recovery_minutes"] > trace_normal.content["estimated_recovery_minutes"]
        )

    def test_shift_attention_priming_reduces_penalty(
        self, default_state: CognitiveState, primed_state: CognitiveState
    ) -> None:
        """High priming should reduce context switch penalty."""
        trace_normal, _ = shift_attention("related_task", default_state)
        trace_primed, _ = shift_attention("related_task", primed_state)
        # Primed state should have higher activation strength (easier shift)
        assert trace_primed.activation_strength > trace_normal.activation_strength

    def test_shift_attention_resets_priming(self, primed_state: CognitiveState) -> None:
        """Shifting attention should reset priming state."""
        _, new_state = shift_attention("new_context", primed_state)
        assert new_state.background_factors[BackgroundFactor.PRIMING_STATE] == 0.0


# =============================================================================
# MATCH_PATTERN FUNCTION TESTS
# =============================================================================


class TestMatchPattern:
    """Tests for the match_pattern cognitive function."""

    def test_match_pattern_returns_trace_and_state(self, default_state: CognitiveState) -> None:
        """Match pattern should return a tuple of (CognitiveTrace, CognitiveState)."""
        trace, new_state = match_pattern("code_snippet", "singleton_pattern", default_state)
        assert isinstance(trace, CognitiveTrace)
        assert isinstance(new_state, CognitiveState)

    def test_match_pattern_event_type(self, default_state: CognitiveState) -> None:
        """Match pattern should create a PATTERN_MATCH event."""
        trace, _ = match_pattern("input", "template", default_state)
        assert trace.event == CognitiveEvent.PATTERN_MATCH

    def test_match_pattern_stores_input_and_template(self, default_state: CognitiveState) -> None:
        """Match pattern should store both input and template."""
        trace, _ = match_pattern("bug_report", "null_pointer_pattern", default_state)
        assert trace.content["input"] == "bug_report"
        assert trace.content["template"] == "null_pointer_pattern"

    def test_match_pattern_high_expectation_increases_confidence(self, default_state: CognitiveState) -> None:
        """High expectation should increase match confidence (confirmation bias)."""
        low_exp_state = CognitiveState()
        low_exp_state.background_factors[BackgroundFactor.EXPECTATION_SET] = 0.2

        high_exp_state = CognitiveState()
        high_exp_state.background_factors[BackgroundFactor.EXPECTATION_SET] = 0.9

        trace_low, _ = match_pattern("code", "bug", low_exp_state)
        trace_high, _ = match_pattern("code", "bug", high_exp_state)

        assert trace_high.content["match_confidence"] > trace_low.content["match_confidence"]

    def test_match_pattern_detects_confirmation_bias_risk(self, default_state: CognitiveState) -> None:
        """High expectation should flag confirmation bias risk."""
        default_state.background_factors[BackgroundFactor.EXPECTATION_SET] = 0.8
        trace, _ = match_pattern("input", "template", default_state)
        assert trace.content["confirmation_bias_risk"] is True

    def test_match_pattern_strengthens_habit(self, default_state: CognitiveState) -> None:
        """Pattern matching should strengthen habit."""
        initial_habit = default_state.background_factors[BackgroundFactor.HABIT_STRENGTH]
        _, new_state = match_pattern("input", "template", default_state)
        assert new_state.background_factors[BackgroundFactor.HABIT_STRENGTH] > initial_habit


# =============================================================================
# TAG_EMOTION FUNCTION TESTS
# =============================================================================


class TestTagEmotion:
    """Tests for the tag_emotion cognitive function."""

    def test_tag_emotion_returns_trace_and_state(self, default_state: CognitiveState) -> None:
        """Tag emotion should return a tuple of (CognitiveTrace, CognitiveState)."""
        trace, new_state = tag_emotion("pr_comment", valence=0.5, intensity=0.6, state=default_state)
        assert isinstance(trace, CognitiveTrace)
        assert isinstance(new_state, CognitiveState)

    def test_tag_emotion_event_type(self, default_state: CognitiveState) -> None:
        """Tag emotion should create an EMOTIONAL_TAG event."""
        trace, _ = tag_emotion("content", 0.5, 0.5, default_state)
        assert trace.event == CognitiveEvent.EMOTIONAL_TAG

    def test_tag_emotion_clamps_intensity(self, default_state: CognitiveState) -> None:
        """Final intensity should be clamped to [0, 1]."""
        # Very high initial intensity that would exceed 1.0 after modulation
        trace, _ = tag_emotion("exciting_news", valence=1.0, intensity=2.0, state=default_state)
        assert 0.0 <= trace.content["final_intensity"] <= 1.0
        assert 0.0 <= trace.activation_strength <= 1.0

    def test_tag_emotion_mood_congruence_amplification(self, default_state: CognitiveState) -> None:
        """Congruent mood should amplify intensity."""
        positive_mood_state = CognitiveState()
        positive_mood_state.background_factors[BackgroundFactor.MOOD_VALENCE] = 0.8

        neutral_mood_state = CognitiveState()
        neutral_mood_state.background_factors[BackgroundFactor.MOOD_VALENCE] = 0.0

        trace_congruent, _ = tag_emotion("good_news", valence=0.5, intensity=0.5, state=positive_mood_state)
        trace_neutral, _ = tag_emotion("good_news", valence=0.5, intensity=0.5, state=neutral_mood_state)

        assert trace_congruent.content["final_intensity"] > trace_neutral.content["final_intensity"]

    def test_tag_emotion_fatigue_dampens_intensity(self, fatigued_state: CognitiveState) -> None:
        """High fatigue should dampen emotional intensity."""
        fresh_state = CognitiveState()
        fresh_state.background_factors[BackgroundFactor.FATIGUE_ACCUMULATION] = 0.1

        trace_fatigued, _ = tag_emotion("news", 0.5, 0.5, fatigued_state)
        trace_fresh, _ = tag_emotion("news", 0.5, 0.5, fresh_state)

        assert trace_fatigued.content["final_intensity"] < trace_fresh.content["final_intensity"]

    def test_tag_emotion_burnout_risk_flag(self, fatigued_state: CognitiveState) -> None:
        """High fatigue should flag burnout risk."""
        trace, _ = tag_emotion("feedback", 0.0, 0.5, fatigued_state)
        assert trace.content["burnout_risk"] is True

    def test_tag_emotion_shifts_mood(self, default_state: CognitiveState) -> None:
        """Emotional tagging should shift mood based on valence and intensity."""
        initial_mood = default_state.background_factors[BackgroundFactor.MOOD_VALENCE]
        _, new_state = tag_emotion("positive_feedback", valence=0.8, intensity=0.7, state=default_state)
        # Positive valence should increase mood
        assert new_state.background_factors[BackgroundFactor.MOOD_VALENCE] > initial_mood

    def test_tag_emotion_stores_original_intensity(self, default_state: CognitiveState) -> None:
        """Trace should store both original and final intensity."""
        trace, _ = tag_emotion("content", 0.5, 0.7, default_state)
        assert "original_intensity" in trace.content
        assert trace.content["original_intensity"] == 0.7


# =============================================================================
# PREPARE_MOTOR FUNCTION TESTS
# =============================================================================


class TestPrepareMotor:
    """Tests for the prepare_motor cognitive function."""

    def test_prepare_motor_returns_trace_and_state(self, default_state: CognitiveState) -> None:
        """Prepare motor should return a tuple of (CognitiveTrace, CognitiveState)."""
        trace, new_state = prepare_motor("type_code", default_state)
        assert isinstance(trace, CognitiveTrace)
        assert isinstance(new_state, CognitiveState)

    def test_prepare_motor_event_type(self, default_state: CognitiveState) -> None:
        """Prepare motor should create a MOTOR_PREPARATION event."""
        trace, _ = prepare_motor("action", default_state)
        assert trace.event == CognitiveEvent.MOTOR_PREPARATION

    def test_prepare_motor_readiness_in_valid_range(self, default_state: CognitiveState) -> None:
        """Readiness should be clamped to [0, 1]."""
        trace, _ = prepare_motor("action", default_state)
        assert 0.0 <= trace.content["readiness"] <= 1.0

    def test_prepare_motor_habit_increases_speed(self, default_state: CognitiveState) -> None:
        """High habit strength should increase preparation speed."""
        low_habit_state = CognitiveState()
        low_habit_state.background_factors[BackgroundFactor.HABIT_STRENGTH] = 0.1

        high_habit_state = CognitiveState()
        high_habit_state.background_factors[BackgroundFactor.HABIT_STRENGTH] = 0.9

        trace_low, _ = prepare_motor("git_commit", low_habit_state)
        trace_high, _ = prepare_motor("git_commit", high_habit_state)

        assert trace_high.content["readiness"] > trace_low.content["readiness"]

    def test_prepare_motor_high_load_slows_preparation(self, high_load_state: CognitiveState) -> None:
        """High cognitive load should slow preparation."""
        low_load_state = CognitiveState()
        low_load_state.background_factors[BackgroundFactor.COGNITIVE_LOAD] = 0.1

        trace_high_load, _ = prepare_motor("deploy", high_load_state)
        trace_low_load, _ = prepare_motor("deploy", low_load_state)

        assert trace_high_load.content["readiness"] < trace_low_load.content["readiness"]

    def test_prepare_motor_warmup_needed_flag(self, default_state: CognitiveState) -> None:
        """Low readiness should flag warmup needed."""
        # Create state that will produce low readiness
        low_readiness_state = CognitiveState()
        low_readiness_state.background_factors[BackgroundFactor.HABIT_STRENGTH] = 0.0
        low_readiness_state.background_factors[BackgroundFactor.COGNITIVE_LOAD] = 0.9
        low_readiness_state.background_factors[BackgroundFactor.AROUSAL_LEVEL] = 0.0

        trace, _ = prepare_motor("unfamiliar_action", low_readiness_state)
        assert trace.content["warmup_needed"] is True

    def test_prepare_motor_yerkes_dodson_effect(self, default_state: CognitiveState) -> None:
        """Moderate arousal should be optimal (Yerkes-Dodson law)."""
        low_arousal_state = CognitiveState()
        low_arousal_state.background_factors[BackgroundFactor.AROUSAL_LEVEL] = 0.1

        optimal_arousal_state = CognitiveState()
        optimal_arousal_state.background_factors[BackgroundFactor.AROUSAL_LEVEL] = 0.5

        high_arousal_state = CognitiveState()
        high_arousal_state.background_factors[BackgroundFactor.AROUSAL_LEVEL] = 0.9

        trace_low, _ = prepare_motor("action", low_arousal_state)
        trace_optimal, _ = prepare_motor("action", optimal_arousal_state)
        trace_high, _ = prepare_motor("action", high_arousal_state)

        # Optimal arousal should have best readiness
        assert trace_optimal.content["readiness"] >= trace_low.content["readiness"]
        assert trace_optimal.content["readiness"] >= trace_high.content["readiness"]


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestCognitiveChains:
    """Tests for sequences of cognitive operations."""

    def test_perception_to_pattern_match_chain(self, default_state: CognitiveState) -> None:
        """Perceive then pattern match should accumulate traces."""
        _, state_after_perceive = perceive("code_snippet", default_state)
        _, state_after_match = match_pattern("code_snippet", "bug_pattern", state_after_perceive)

        assert len(state_after_match.recent_traces) == 2
        assert state_after_match.recent_traces[0].event == CognitiveEvent.PERCEPTION
        assert state_after_match.recent_traces[1].event == CognitiveEvent.PATTERN_MATCH

    def test_context_switch_accumulates_load(self, default_state: CognitiveState) -> None:
        """Multiple attention shifts should accumulate cognitive load."""
        state = default_state
        for i in range(5):
            _, state = shift_attention(f"task_{i}", state)

        # Load should have increased significantly
        assert state.background_factors[BackgroundFactor.COGNITIVE_LOAD] > 0.7

    def test_emotional_chain_affects_mood(self, default_state: CognitiveState) -> None:
        """Series of negative emotions should shift mood negative."""
        state = default_state
        for _ in range(3):
            _, state = tag_emotion("bad_news", valence=-0.5, intensity=0.6, state=state)

        assert state.background_factors[BackgroundFactor.MOOD_VALENCE] < 0.5

    def test_full_code_review_scenario(self, default_state: CognitiveState) -> None:
        """Simulate a code review with multiple cognitive events."""
        state = default_state

        # Open PR (shift attention)
        _, state = shift_attention("pull_request_123", state)

        # Scan code (perceive)
        _, state = perceive("diff_content", state)

        # Recognize pattern (pattern match)
        trace_match, state = match_pattern("diff_content", "potential_bug", state)

        # React emotionally (tag emotion)
        _, state = tag_emotion("found_bug", valence=-0.3, intensity=0.5, state=state)

        # Prepare to comment (motor preparation)
        trace_motor, state = prepare_motor("write_comment", state)

        # Verify state evolution
        assert len(state.recent_traces) == 5
        assert state.attention_focus == "pull_request_123"
        assert trace_match.event == CognitiveEvent.PATTERN_MATCH
        assert trace_motor.event == CognitiveEvent.MOTOR_PREPARATION
