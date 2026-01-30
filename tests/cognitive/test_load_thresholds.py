"""Test suite for cognitive load thresholds and scaffolding triggers."""

import pytest

from cognitive.light_of_the_seven.cognitive_layer.cognitive_load.load_estimator import CognitiveLoadEstimator


class TestLoadThresholds:
    """Test suite for load threshold validation."""

    @pytest.fixture
    def estimator(self):
        """Create load estimator instance for testing."""
        return CognitiveLoadEstimator()

    def test_scaffolding_threshold_detection(self, estimator):
        """Test load > 7.0 threshold for scaffolding."""
        # Just below threshold
        below_threshold_operation = {
            "information_density": 0.6,
            "novelty": 0.5,
            "complexity": 0.6,
            "time_pressure": 0.2,
            "split_attention": 0.1,
            "element_interactivity": 0.4,
        }
        load_below = estimator.estimate_load(below_threshold_operation)
        assert load_below <= 7.0, f"Load {load_below} should be <= 7.0"

        # Just above threshold
        above_threshold_operation = {
            "information_density": 0.8,
            "novelty": 0.7,
            "complexity": 0.9,
            "time_pressure": 0.6,
            "split_attention": 0.4,
            "element_interactivity": 0.7,
        }
        load_above = estimator.estimate_load(above_threshold_operation)
        assert load_above > 7.0, f"Load {load_above} should be > 7.0"

    def test_threshold_edge_cases(self, estimator):
        """Test threshold boundary conditions."""
        # Exactly at threshold
        threshold_operation = {
            "information_density": 0.7,
            "novelty": 0.7,
            "complexity": 0.7,
            "time_pressure": 0.7,
            "split_attention": 0.7,
            "element_interactivity": 0.7,
        }
        load_at_threshold = estimator.estimate_load(threshold_operation)

        # Should be close to threshold (allowing for rounding)
        assert abs(load_at_threshold - 7.0) < 0.5, f"Load {load_at_threshold} should be near 7.0"

    def test_load_threshold_scenarios(self, estimator):
        """Test realistic scenarios around threshold."""
        # High complexity scenario (should trigger scaffolding)
        high_complexity = {
            "information_density": 0.9,
            "novelty": 0.8,
            "complexity": 0.9,  # Very high
            "time_pressure": 0.7,
            "split_attention": 0.5,
            "element_interactivity": 0.8,
        }
        load = estimator.estimate_load(high_complexity)
        assert load > 7.0, "High complexity should trigger scaffolding"

        # Low complexity scenario (should not trigger scaffolding)
        low_complexity = {
            "information_density": 0.4,
            "novelty": 0.3,
            "complexity": 0.2,  # Very low
            "time_pressure": 0.1,
            "split_attention": 0.1,
            "element_interactivity": 0.3,
        }
        load = estimator.estimate_load(low_complexity)
        assert load < 7.0, "Low complexity should not trigger scaffolding"
