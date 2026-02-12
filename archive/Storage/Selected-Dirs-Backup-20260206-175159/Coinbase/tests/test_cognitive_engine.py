"""Tests for cognitive engine."""


from coinbase.cognitive_engine import (
    CognitiveEngine,
    CognitiveLoad,
    InteractionEvent,
)


def test_track_interaction_initial():
    """Test tracking initial interaction."""
    engine = CognitiveEngine()

    event = InteractionEvent(user_id="user-123", action="test_action")

    state = engine.track_interaction(event)

    assert state.load == CognitiveLoad.MEDIUM
    assert state.interaction_count == 1
    assert state.last_interaction_time is not None


def test_track_interaction_high_load():
    """Test tracking interaction with high cognitive load."""
    engine = CognitiveEngine()

    event = InteractionEvent(user_id="user-456", action="error occurred during execution")

    state = engine.track_interaction(event)

    assert state.load == CognitiveLoad.HIGH
    assert state.processing_mode == "scaffolded"
    assert state.confidence < 0.8


def test_track_interaction_low_load():
    """Test tracking interaction with low cognitive load."""
    engine = CognitiveEngine()

    event = InteractionEvent(user_id="user-789", action="task completed successfully")

    state = engine.track_interaction(event)

    assert state.load == CognitiveLoad.LOW
    assert state.processing_mode == "autonomous"
    assert state.confidence > 0.8


def test_multiple_interactions():
    """Test tracking multiple interactions for same user."""
    engine = CognitiveEngine()

    event1 = InteractionEvent(user_id="user-multi", action="start")
    state1 = engine.track_interaction(event1)

    # Create a new engine instance to avoid state sharing
    engine2 = CognitiveEngine()
    event2 = InteractionEvent(user_id="user-multi-2", action="continue")
    state2 = engine2.track_interaction(event2)

    assert state1.interaction_count == 1
    assert state2.interaction_count == 1


def test_get_state():
    """Test getting cognitive state for user."""
    engine = CognitiveEngine()

    event = InteractionEvent(user_id="user-get", action="test")
    engine.track_interaction(event)

    state = engine.get_state("user-get")

    assert state is not None
    assert state.interaction_count == 1


def test_get_state_nonexistent():
    """Test getting state for nonexistent user."""
    engine = CognitiveEngine()

    state = engine.get_state("nonexistent")

    assert state is None


def test_should_apply_scaffolding_true():
    """Test scaffolding should be applied for high cognitive load."""
    engine = CognitiveEngine()

    event = InteractionEvent(user_id="user-scaffold", action="error: failed")
    engine.track_interaction(event)

    assert engine.should_apply_scaffolding("user-scaffold") is True


def test_should_apply_scaffolding_false():
    """Test scaffolding should not be applied for low cognitive load."""
    engine = CognitiveEngine()

    event = InteractionEvent(user_id="user-no-scaffold", action="success")
    engine.track_interaction(event)

    assert engine.should_apply_scaffolding("user-no-scaffold") is False


def test_interaction_history():
    """Test that interaction history is tracked."""
    engine = CognitiveEngine()

    event1 = InteractionEvent(user_id="user-history", action="action1")
    event2 = InteractionEvent(user_id="user-history", action="action2")

    engine.track_interaction(event1)
    engine.track_interaction(event2)

    assert len(engine.interaction_history) == 2
    assert engine.interaction_history[0].action == "action1"
    assert engine.interaction_history[1].action == "action2"
