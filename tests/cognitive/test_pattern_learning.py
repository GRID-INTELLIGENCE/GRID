"""Tests for AdvancedPatternManager Online Logistic Regression learning.

Covers:
- Empty/null input safety (skeptical default)
- Overflow protection (clamping)
- Learning convergence over iterations
- L2 decay on stale weights
- learning_enabled guard
- JSON serialisability of learning_state
"""

import json
import math

import pytest

from cognition.Pattern import (
    AdvancedPatternManager,
    CognitivePattern,
    PatternType,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def manager() -> AdvancedPatternManager:
    mgr = AdvancedPatternManager(learning_rate=0.1, decay=0.001)
    mgr.enable_learning()
    return mgr


@pytest.fixture
def semantic_pattern(manager: AdvancedPatternManager) -> CognitivePattern:
    """Register a minimal semantic pattern for testing."""
    pattern = manager.create_pattern_from_template(
        pattern_id="test_semantic",
        name="Test Semantic",
        pattern_type=PatternType.SEMANTIC,
        template={"keywords": ["urgent", "error"]},
    )
    return pattern


# ---------------------------------------------------------------------------
# Test: Empty input → low probability (skeptical default)
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestEmptyInputSafety:
    def test_empty_string_low_probability(self, manager: AdvancedPatternManager, semantic_pattern: CognitivePattern) -> None:
        prob = manager.predict_proba("test_semantic", "")
        # Bias is -0.5 → sigmoid(-0.5) ≈ 0.378
        assert prob < 0.5, f"Empty input should be below 0.5, got {prob}"

    def test_none_input_low_probability(self, manager: AdvancedPatternManager, semantic_pattern: CognitivePattern) -> None:
        prob = manager.predict_proba("test_semantic", None)
        assert prob < 0.5, f"None input should be below 0.5, got {prob}"

    def test_unknown_pattern_returns_zero(self, manager: AdvancedPatternManager) -> None:
        prob = manager.predict_proba("nonexistent_pattern", "anything")
        assert prob == 0.0


# ---------------------------------------------------------------------------
# Test: Overflow protection
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestOverflowProtection:
    def test_huge_feature_value_no_crash(self, manager: AdvancedPatternManager, semantic_pattern: CognitivePattern) -> None:
        """Feature value of 1,000,000 must not cause OverflowError."""
        prob = manager.predict_proba("test_semantic", {"extreme_feature": 1_000_000})
        assert 0.0 <= prob <= 1.0

    def test_negative_extreme_no_crash(self, manager: AdvancedPatternManager, semantic_pattern: CognitivePattern) -> None:
        prob = manager.predict_proba("test_semantic", {"extreme_feature": -1_000_000})
        assert 0.0 <= prob <= 1.0

    def test_sigmoid_clamping(self) -> None:
        """Verify _sigmoid clamps properly."""
        assert AdvancedPatternManager._sigmoid(1000.0) == pytest.approx(1.0, abs=1e-6)
        assert AdvancedPatternManager._sigmoid(-1000.0) == pytest.approx(0.0, abs=1e-6)
        assert AdvancedPatternManager._sigmoid(0.0) == pytest.approx(0.5, abs=1e-6)


# ---------------------------------------------------------------------------
# Test: Learning convergence
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestLearningConvergence:
    def test_positive_training_increases_confidence(
        self, manager: AdvancedPatternManager, semantic_pattern: CognitivePattern
    ) -> None:
        """After training on 'urgent error' with label=1.0, probability should increase."""
        initial_prob = manager.predict_proba("test_semantic", "urgent error system")

        for _ in range(20):
            manager.learn_from_match("test_semantic", "urgent error system", actual_label=1.0)

        final_prob = manager.predict_proba("test_semantic", "urgent error system")
        assert final_prob > initial_prob, f"Expected increase: {initial_prob} → {final_prob}"
        assert final_prob > 0.7, f"Expected >0.7 after 20 iterations, got {final_prob}"

    def test_negative_training_decreases_confidence(
        self, manager: AdvancedPatternManager, semantic_pattern: CognitivePattern
    ) -> None:
        """Training with label=0.0 should push probability down."""
        # First train up
        for _ in range(10):
            manager.learn_from_match("test_semantic", "urgent error", actual_label=1.0)

        mid_prob = manager.predict_proba("test_semantic", "urgent error")
        assert mid_prob > 0.5

        # Now train back down
        for _ in range(20):
            manager.learn_from_match("test_semantic", "urgent error", actual_label=0.0)

        final_prob = manager.predict_proba("test_semantic", "urgent error")
        assert final_prob < mid_prob, f"Expected decrease: {mid_prob} → {final_prob}"

    def test_samples_seen_increments(
        self, manager: AdvancedPatternManager, semantic_pattern: CognitivePattern
    ) -> None:
        for _ in range(5):
            manager.learn_from_match("test_semantic", "urgent", actual_label=1.0)

        state = semantic_pattern.learning_state
        assert state is not None
        assert state["samples_seen"] == 5


# ---------------------------------------------------------------------------
# Test: L2 decay reduces weights on active features
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestL2Decay:
    def test_decay_shrinks_weights(self) -> None:
        """With decay > 0 and error ≈ 0, weights should shrink slightly."""
        mgr = AdvancedPatternManager(learning_rate=0.1, decay=0.1)  # Strong decay
        mgr.enable_learning()
        pattern = mgr.create_pattern_from_template(
            pattern_id="decay_test",
            name="Decay Test",
            pattern_type=PatternType.SEMANTIC,
            template={"keywords": ["alpha"]},
        )

        # First train the weight up
        for _ in range(20):
            mgr.learn_from_match("decay_test", "alpha", actual_label=1.0)

        state = pattern.learning_state
        assert state is not None
        w_after_train = state["weights"].get("alpha", 0.0)
        assert w_after_train > 0.0, "Weight should be positive after positive training"

        # Now train with probability ≈ label, so error ≈ 0 → decay dominates
        # We do this by sending neutral data that the model already agrees with
        prob_before = mgr.predict_proba("decay_test", "alpha")

        # Train with label matching current prediction (error ≈ 0)
        mgr.learn_from_match("decay_test", "alpha", actual_label=prob_before)

        w_after_decay = state["weights"]["alpha"]
        # With near-zero error, decay should have shrunk the weight
        assert w_after_decay < w_after_train, (
            f"Decay should shrink weight: {w_after_train} → {w_after_decay}"
        )


# ---------------------------------------------------------------------------
# Test: learning_enabled guard
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestLearningDisabled:
    def test_learn_noop_when_disabled(self) -> None:
        mgr = AdvancedPatternManager()
        # learning_enabled is False by default
        pattern = mgr.create_pattern_from_template(
            pattern_id="disabled_test",
            name="Disabled Test",
            pattern_type=PatternType.SEMANTIC,
            template={"keywords": ["test"]},
        )

        mgr.learn_from_match("disabled_test", "test data", actual_label=1.0)

        # learning_state should NOT have been initialised
        assert pattern.learning_state is None
        assert len(mgr.match_history) == 0


# ---------------------------------------------------------------------------
# Test: JSON serialisability
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestJSONPersistence:
    def test_learning_state_is_json_serialisable(
        self, manager: AdvancedPatternManager, semantic_pattern: CognitivePattern
    ) -> None:
        """learning_state must survive json.dumps without error."""
        for _ in range(5):
            manager.learn_from_match("test_semantic", "urgent error", actual_label=1.0)

        state = semantic_pattern.learning_state
        assert state is not None

        # Must not raise
        serialised = json.dumps(state)
        assert isinstance(serialised, str)

        # Round-trip
        restored = json.loads(serialised)
        assert restored["bias"] == pytest.approx(state["bias"])
        assert restored["samples_seen"] == state["samples_seen"]
        for key, val in state["weights"].items():
            assert restored["weights"][key] == pytest.approx(val)

    def test_no_nan_or_inf_in_weights(
        self, manager: AdvancedPatternManager, semantic_pattern: CognitivePattern
    ) -> None:
        """Weights must never contain NaN or Infinity."""
        for _ in range(50):
            manager.learn_from_match("test_semantic", "urgent error system", actual_label=1.0)
        for _ in range(50):
            manager.learn_from_match("test_semantic", "normal routine check", actual_label=0.0)

        state = semantic_pattern.learning_state
        assert state is not None

        assert not math.isnan(state["bias"])
        assert not math.isinf(state["bias"])
        for val in state["weights"].values():
            assert not math.isnan(val), "NaN found in weights"
            assert not math.isinf(val), "Inf found in weights"
