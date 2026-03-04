"""
Tests for pattern_manager.py — resonance learning additions.
"""

import pytest

from cognitive.pattern_manager import AdvancedPatternManager, PatternModel


@pytest.fixture
def manager():
    pm = AdvancedPatternManager()
    pm.register_pattern("p1", "Test Pattern", "flow", initial_confidence=0.5)
    return pm


def test_pattern_model_has_resonance_history():
    model = PatternModel(pattern_id="x", name="X", pattern_type="flow")
    assert model.resonance_history == []


def test_learn_from_resonance_basic(manager):
    update = manager.learn_from_resonance(
        pattern_id="p1",
        features={"connection_strength": 0.7},
        connection_strength=0.7,
        semantic_similarity=0.6,
        emotional_amplification=0.1,
    )
    assert update is not None
    assert update.was_correct is True
    assert update.user_feedback == "resonance"
    assert update.confidence_adjustment > 0


def test_learn_from_resonance_not_found(manager):
    result = manager.learn_from_resonance(
        pattern_id="nonexistent",
        features={},
        connection_strength=0.5,
    )
    assert result is None


def test_learn_from_resonance_gradient(manager):
    """connection_strength * learning_rate = confidence_delta."""
    model = manager.get_pattern_model("p1")
    old_conf = model.confidence

    manager.learn_from_resonance(
        pattern_id="p1",
        features={},
        connection_strength=0.8,
    )

    # delta = 0.8 * 0.5 (learning_rate) = 0.4
    expected = old_conf + 0.8 * manager._learning_rate
    assert abs(model.confidence - expected) < 1e-9


def test_learn_from_resonance_caps_at_1(manager):
    model = manager.get_pattern_model("p1")
    model.confidence = 0.9

    manager.learn_from_resonance(
        pattern_id="p1",
        features={},
        connection_strength=1.0,
    )

    assert model.confidence <= 1.0


def test_learn_from_resonance_records_history(manager):
    manager.learn_from_resonance(
        pattern_id="p1",
        features={"key": "value"},
        connection_strength=0.5,
        semantic_similarity=0.4,
        emotional_amplification=0.3,
    )

    model = manager.get_pattern_model("p1")
    assert len(model.resonance_history) == 1
    entry = model.resonance_history[0]
    assert entry["connection_strength"] == 0.5
    assert entry["semantic_similarity"] == 0.4
    assert entry["emotional_amplification"] == 0.3
    assert "timestamp" in entry


def test_learn_from_resonance_increments_usage(manager):
    model = manager.get_pattern_model("p1")
    old_count = model.usage_count

    manager.learn_from_resonance(
        pattern_id="p1",
        features={},
        connection_strength=0.5,
    )

    assert model.usage_count == old_count + 1


def test_update_pattern_parameters(manager):
    """_update_pattern_parameters should EMA numeric features."""
    model = manager.get_pattern_model("p1")
    model.parameters["x"] = 10.0

    manager._update_pattern_parameters(model, {"x": 20.0, "name": "ignored"})

    # EMA: 10.0 + 0.5 * (20.0 - 10.0) = 15.0
    assert abs(model.parameters["x"] - 15.0) < 1e-9


def test_update_pattern_parameters_new_key(manager):
    model = manager.get_pattern_model("p1")
    manager._update_pattern_parameters(model, {"new_key": 42.0})
    assert model.parameters["new_key"] == 42.0
