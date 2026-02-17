"""Test suite for cognitive load estimator functionality."""

import pytest

from cognitive.light_of_the_seven.cognitive_layer.cognitive_load.load_estimator import (
    CognitiveLoadEstimator,
)
from cognitive.light_of_the_seven.cognitive_layer.schemas.cognitive_state import CognitiveLoadType
from cognitive.light_of_the_seven.cognitive_layer.schemas.user_cognitive_profile import (
    ExpertiseLevel,
    UserCognitiveProfile,
)


class TestCognitiveLoadEstimator:
    """Test suite for CognitiveLoadEstimator class."""

    @pytest.fixture
    def estimator(self):
        """Create load estimator instance for testing."""
        return CognitiveLoadEstimator()

    def test_estimate_load_basic_calculation(self, estimator):
        """Test basic weighted load calculation."""
        operation = {
            "information_density": 0.5,
            "novelty": 0.5,
            "complexity": 0.5,
            "time_pressure": 0.0,
            "split_attention": 0.0,
            "element_interactivity": 0.5,
        }

        # Expected: (0.5*0.25 + 0.5*0.20 + 0.5*0.25 + 0.0*0.15 + 0.0*0.10 + 0.5*0.05) * 10
        # = (0.125 + 0.10 + 0.125 + 0.0 + 0.0 + 0.025) * 10 = 0.375 * 10 = 3.75
        expected_load = 3.75
        actual_load = estimator.estimate_load(operation)

        assert abs(actual_load - expected_load) < 0.01, f"Expected {expected_load}, got {actual_load}"

    def test_estimate_load_edge_cases(self, estimator):
        """Test edge cases: minimum and maximum load."""
        # Minimum load (all zeros)
        min_operation = {
            "information_density": 0.0,
            "novelty": 0.0,
            "complexity": 0.0,
            "time_pressure": 0.0,
            "split_attention": 0.0,
            "element_interactivity": 0.0,
        }
        assert estimator.estimate_load(min_operation) == 0.0

        # Maximum load (all ones)
        max_operation = {
            "information_density": 1.0,
            "novelty": 1.0,
            "complexity": 1.0,
            "time_pressure": 1.0,
            "split_attention": 1.0,
            "element_interactivity": 1.0,
        }
        assert estimator.estimate_load(max_operation) == 10.0  # Capped at 10

    def test_factor_weights(self, estimator):
        """Test each factor's weight contribution."""
        # Test information density weight (25%)
        operation_density = {
            "information_density": 1.0,
            "novelty": 0.0,
            "complexity": 0.0,
            "time_pressure": 0.0,
            "split_attention": 0.0,
            "element_interactivity": 0.0,
        }
        load_density = estimator.estimate_load(operation_density)
        assert abs(load_density - 2.5) < 0.01  # 1.0 * 0.25 * 10 = 2.5

        # Test novelty weight (20%)
        operation_novelty = {
            "information_density": 0.0,
            "novelty": 1.0,
            "complexity": 0.0,
            "time_pressure": 0.0,
            "split_attention": 0.0,
            "element_interactivity": 0.0,
        }
        load_novelty = estimator.estimate_load(operation_novelty)
        assert abs(load_novelty - 2.0) < 0.01  # 1.0 * 0.20 * 10 = 2.0

        # Test complexity weight (25%)
        operation_complexity = {
            "information_density": 0.0,
            "novelty": 0.0,
            "complexity": 1.0,
            "time_pressure": 0.0,
            "split_attention": 0.0,
            "element_interactivity": 0.0,
        }
        load_complexity = estimator.estimate_load(operation_complexity)
        assert abs(load_complexity - 2.5) < 0.01  # 1.0 * 0.25 * 10 = 2.5

        # Test time pressure weight (15%)
        operation_time_pressure = {
            "information_density": 0.0,
            "novelty": 0.0,
            "complexity": 0.0,
            "time_pressure": 1.0,
            "split_attention": 0.0,
            "element_interactivity": 0.0,
        }
        load_time_pressure = estimator.estimate_load(operation_time_pressure)
        assert abs(load_time_pressure - 1.5) < 0.01  # 1.0 * 0.15 * 10 = 1.5

        # Test split attention weight (10%)
        operation_split_attention = {
            "information_density": 0.0,
            "novelty": 0.0,
            "complexity": 0.0,
            "time_pressure": 0.0,
            "split_attention": 1.0,
            "element_interactivity": 0.0,
        }
        load_split_attention = estimator.estimate_load(operation_split_attention)
        assert abs(load_split_attention - 1.0) < 0.01  # 1.0 * 0.10 * 10 = 1.0

        # Test element interactivity weight (5%)
        operation_element_interactivity = {
            "information_density": 0.0,
            "novelty": 0.0,
            "complexity": 0.0,
            "time_pressure": 0.0,
            "split_attention": 0.0,
            "element_interactivity": 1.0,
        }
        load_element_interactivity = estimator.estimate_load(operation_element_interactivity)
        assert abs(load_element_interactivity - 0.5) < 0.01  # 1.0 * 0.05 * 10 = 0.5

    def test_factor_interactions(self, estimator):
        """Test how factors combine."""
        # High complexity + high time pressure should increase load significantly
        high_stress = {
            "information_density": 0.7,
            "novelty": 0.6,
            "complexity": 0.9,  # High complexity
            "time_pressure": 0.8,  # High time pressure
            "split_attention": 0.3,
            "element_interactivity": 0.6,
        }

        load_high_stress = estimator.estimate_load(high_stress)
        assert load_high_stress > 7.0, "High stress should result in high load"

        # Low complexity + low time pressure should result in low load
        low_stress = {
            "information_density": 0.3,
            "novelty": 0.2,
            "complexity": 0.1,  # Low complexity
            "time_pressure": 0.0,  # No time pressure
            "split_attention": 0.1,
            "element_interactivity": 0.2,
        }

        load_low_stress = estimator.estimate_load(low_stress)
        assert load_low_stress < 4.0, "Low stress should result in low load"

    def test_expertise_level_adjustments(self, estimator):
        """Test load reduction for expert users."""
        operation = {
            "information_density": 0.7,
            "novelty": 0.6,
            "complexity": 0.8,
            "time_pressure": 0.3,
            "split_attention": 0.2,
            "element_interactivity": 0.5,
        }

        base_load = estimator.estimate_load(operation)

        # Load with expert profile (should be 0.8x)
        expert_profile = UserCognitiveProfile(
            user_id="test_expert", expertise_level=ExpertiseLevel.EXPERT, working_memory_capacity=1.0
        )
        expert_load = estimator.estimate_load(operation, expert_profile)
        assert abs(expert_load - (base_load * 0.8)) < 0.01

        # Load with advanced profile (should be 0.8x)
        advanced_profile = UserCognitiveProfile(
            user_id="test_advanced", expertise_level=ExpertiseLevel.ADVANCED, working_memory_capacity=1.0
        )
        advanced_load = estimator.estimate_load(operation, advanced_profile)
        assert abs(advanced_load - (base_load * 0.8)) < 0.01

        # Load with intermediate profile (should be unchanged)
        intermediate_profile = UserCognitiveProfile(
            user_id="test_intermediate", expertise_level=ExpertiseLevel.INTERMEDIATE, working_memory_capacity=1.0
        )
        intermediate_load = estimator.estimate_load(operation, intermediate_profile)
        assert abs(intermediate_load - base_load) < 0.01

    def test_working_memory_capacity_adjustments(self, estimator):
        """Test load adjustment based on working memory capacity."""
        operation = {
            "information_density": 0.6,
            "novelty": 0.5,
            "complexity": 0.6,
            "time_pressure": 0.2,
            "split_attention": 0.1,
            "element_interactivity": 0.4,
        }

        # High capacity user (should reduce load)
        high_capacity_profile = UserCognitiveProfile(
            user_id="test_high_capacity",
            expertise_level=ExpertiseLevel.INTERMEDIATE,
            working_memory_capacity=0.9,  # Within valid range (0-1)
        )
        high_capacity_load = estimator.estimate_load(operation, high_capacity_profile)

        # Low capacity user (should increase load)
        low_capacity_profile = UserCognitiveProfile(
            user_id="test_low_capacity",
            expertise_level=ExpertiseLevel.INTERMEDIATE,
            working_memory_capacity=0.3,  # Within valid range (0-1)
        )
        low_capacity_load = estimator.estimate_load(operation, low_capacity_profile)

        assert high_capacity_load < low_capacity_load, "High capacity should reduce perceived load"

    def test_load_type_classification(self, estimator):
        """Test cognitive load type detection."""
        # Intrinsic load (high element interactivity)
        intrinsic_operation = {
            "element_interactivity": 0.8,  # > 0.7 threshold
            "split_attention": 0.3,
            "novelty": 0.4,
            "complexity": 0.6,
        }
        load_type = estimator.estimate_load_type(intrinsic_operation)
        assert load_type == CognitiveLoadType.INTRINSIC

        # Extraneous load (high split attention)
        extraneous_operation = {
            "element_interactivity": 0.4,
            "split_attention": 0.7,  # > 0.5 threshold
            "novelty": 0.3,
            "complexity": 0.5,
        }
        load_type = estimator.estimate_load_type(extraneous_operation)
        assert load_type == CognitiveLoadType.EXTRINSIC

        # Germane load (high novelty, low complexity)
        germane_operation = {
            "element_interactivity": 0.3,
            "split_attention": 0.2,
            "novelty": 0.8,  # > 0.6 threshold
            "complexity": 0.3,  # < 0.5 threshold
        }
        load_type = estimator.estimate_load_type(germane_operation)
        assert load_type == CognitiveLoadType.GERMANE

    def test_working_memory_usage_calculation(self, estimator):
        """Test working memory usage estimation."""
        operation = {"information": {"item_count": 9}}  # More than Miller's magic number 7

        usage = estimator.estimate_working_memory_usage(operation)
        assert usage > 0.0, "Working memory usage should be > 0"
        assert usage <= 1.0, "Working memory usage should be <= 1.0"

        # Test with fewer items
        low_items_operation = {"information": {"item_count": 3}}  # Less than Miller's magic number

        low_usage = estimator.estimate_working_memory_usage(low_items_operation)
        assert low_usage <= usage, "Fewer items should result in lower or equal usage"

    def test_working_memory_user_capacity_adjustment(self, estimator):
        """Test working memory usage adjustment for user capacity."""
        operation = {"information": {"item_count": 10}}

        # High capacity user
        high_capacity_profile = UserCognitiveProfile(
            user_id="test_high_mem",
            working_memory_capacity=0.9,  # Within valid range (0-1)
        )
        high_usage = estimator.estimate_working_memory_usage(operation, high_capacity_profile)

        # Low capacity user
        low_capacity_profile = UserCognitiveProfile(
            user_id="test_low_mem",
            working_memory_capacity=0.3,  # Within valid range (0-1)
        )
        low_usage = estimator.estimate_working_memory_usage(operation, low_capacity_profile)

        assert high_usage < low_usage, "High capacity should result in lower relative usage"

    def test_create_cognitive_state(self, estimator):
        """Test cognitive state creation."""
        operation = {
            "information_density": 0.6,
            "novelty": 0.5,
            "complexity": 0.7,
            "time_pressure": 0.2,
            "split_attention": 0.1,
            "element_interactivity": 0.4,
        }

        cognitive_state = estimator.create_cognitive_state(operation)

        assert cognitive_state.estimated_load > 0.0
        assert cognitive_state.estimated_load <= 10.0
        assert cognitive_state.load_type in [
            CognitiveLoadType.INTRINSIC,
            CognitiveLoadType.EXTRINSIC,
            CognitiveLoadType.GERMANE,
        ]
        assert cognitive_state.working_memory_usage >= 0.0
        assert cognitive_state.working_memory_usage <= 1.0
        assert cognitive_state.decision_complexity == 0.7
        assert cognitive_state.time_pressure == 0.2

    def test_is_load_acceptable(self, estimator):
        """Test load acceptability checking."""
        # Low load should be acceptable
        assert estimator.is_load_acceptable(3.0) is True

        # High load should not be acceptable
        assert estimator.is_load_acceptable(8.0) is False

        # Edge case at threshold (7.0)
        assert estimator.is_load_acceptable(7.0) is True
        assert estimator.is_load_acceptable(7.1) is False
