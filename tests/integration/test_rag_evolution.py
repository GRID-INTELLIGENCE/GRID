"""
Comprehensive test suite for RAG Evolution Layer.

Tests the core state management and persistence components including:
- FibonacciEvolutionEngine: Dynamic optimization patterns
- VersionState: Version management and evolution tracking
- LandscapeDetector: State change detection
- RealTimeAdapter: Adaptation mechanisms
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

# Import necessary components
from grid.evolution import (
    AdaptationState,
    DynamicWeightNetwork,
    FibonacciEvolutionEngine,
    FibonacciEvolutionState,
    LandscapeDetector,
    LandscapeShift,
    LandscapeSnapshot,
    RealTimeAdapter,
    VersionState,
    WeightUpdate,
)


class TestFibonacciEvolution:
    """Test Fibonacci evolution patterns and state management."""

    @pytest.fixture
    def evolution_engine(self):
        """Create FibonacciEvolutionEngine instance."""
        return FibonacciEvolutionEngine()

    def test_sequence_generation(self, evolution_engine):
        """Test Fibonacci sequence generation."""
        sequence = evolution_engine.generate_sequence(10)

        assert len(sequence) == 10
        assert sequence == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]

    def test_state_evolution(self, evolution_engine):
        """Test state evolution with Fibonacci patterns."""
        initial_state = Mock(complexity=0.5, stability=0.7, adaptability=0.3)

        evolved_state = evolution_engine.evolve_state(initial_state)

        assert evolved_state.complexity != initial_state.complexity
        assert evolved_state.stability != initial_state.stability
        assert evolved_state.adaptability != initial_state.adaptability

    def test_state_persistence(self, evolution_engine):
        """Test state persistence and loading."""
        initial_state = FibonacciEvolutionState(complexity=0.6, stability=0.8, adaptability=0.4)

        # Save state
        with tempfile.NamedTemporaryFile(suffix=".json") as temp_file:
            temp_path = Path(temp_file.name)
            evolution_engine.save_state(initial_state, temp_path)

            # Load state
            loaded_state = evolution_engine.load_state(temp_path)

            assert loaded_state.complexity == initial_state.complexity
            assert loaded_state.stability == initial_state.stability
            assert loaded_state.adaptability == initial_state.adaptability

    def test_adaptation_feedback(self, evolution_engine):
        """Test adaptation feedback loop."""
        initial_state = FibonacciEvolutionState(complexity=0.5, stability=0.5, adaptability=0.5)

        # Simulate positive feedback
        feedback = {"complexity": 0.6, "stability": 0.7, "adaptability": 0.4}

        adapted_state = evolution_engine.adapt_state(initial_state, feedback)

        assert adapted_state.complexity > initial_state.complexity
        assert adapted_state.stability > initial_state.stability
        assert adapted_state.adaptability < initial_state.adaptability


class TestVersionState:
    """Test version state management and evolution tracking."""

    @pytest.fixture
    def version_state(self):
        """Create VersionState instance."""
        return VersionState(current_version="1.0.0", evolution_sequence=[0, 1, 1, 2, 3])

    def test_version_increment(self, version_state):
        """Test version increment logic."""
        version_state.increment_version()

        assert version_state.current_version == "1.0.1"
        assert len(version_state.evolution_sequence) == 6
        assert version_state.evolution_sequence[-1] == 5

    def test_version_rollback(self, version_state):
        """Test version rollback capability."""
        version_state.increment_version()  # 1.0.1
        version_state.increment_version()  # 1.0.2

        version_state.rollback_version()

        assert version_state.current_version == "1.0.1"
        assert len(version_state.evolution_sequence) == 7
        assert version_state.evolution_sequence[-1] == 3

    def test_state_compatibility(self, version_state):
        """Test state compatibility checking."""
        compatible_state = VersionState(current_version="1.0.1", evolution_sequence=[0, 1, 1, 2, 3, 5])

        incompatible_state = VersionState(current_version="2.0.0", evolution_sequence=[0, 1, 1, 2, 3, 5, 8])

        assert version_state.is_compatible_with(compatible_state)
        assert not version_state.is_compatible_with(incompatible_state)


class TestLandscapeDetection:
    """Test landscape detection and state change analysis."""

    @pytest.fixture
    def landscape_detector(self):
        """Create LandscapeDetector instance."""
        return LandscapeDetector()

    def test_landscape_capture(self, landscape_detector):
        """Test landscape capture and snapshot creation."""
        mock_state = {
            "component1": {"status": "active", "load": 0.7},
            "component2": {"status": "inactive", "load": 0.2},
        }

        snapshot = landscape_detector.capture_landscape(mock_state)

        assert isinstance(snapshot, LandscapeSnapshot)
        assert len(snapshot.components) == 2
        assert "component1" in snapshot.components
        assert "component2" in snapshot.components

    def test_shift_detection(self, landscape_detector):
        """Test landscape shift detection."""
        initial_state = {"component1": {"status": "active", "load": 0.7}}

        changed_state = {
            "component1": {"status": "active", "load": 0.9},
            "component2": {"status": "active", "load": 0.1},
        }

        shift = landscape_detector.detect_shift(initial_state, changed_state)

        assert isinstance(shift, LandscapeShift)
        assert len(shift.changes) == 2
        assert "component1" in shift.changes
        assert "component2" in shift.changes

    def test_analysis_integration(self, landscape_detector):
        """Test integration with analysis components."""
        # Test with statistical analyzer
        statistical_analyzer = Mock()
        statistical_analyzer.analyze.return_value = {"trend": "increasing", "confidence": 0.85}

        landscape_detector.register_analyzer("statistical", statistical_analyzer)

        analysis = landscape_detector.analyze_landscape({"component1": {"status": "active", "load": 0.7}})

        assert "statistical" in analysis
        assert analysis["statistical"]["trend"] == "increasing"


class TestRealTimeAdaptation:
    """Test real-time adaptation mechanisms."""

    @pytest.fixture
    def realtime_adapter(self):
        """Create RealTimeAdapter instance."""
        return RealTimeAdapter()

    def test_weight_adaptation(self, realtime_adapter):
        """Test dynamic weight adaptation."""
        initial_weights = {"feature1": 0.5, "feature2": 0.3, "feature3": 0.2}

        # Simulate positive feedback for feature1
        feedback = {"feature1": 0.8, "feature2": 0.4, "feature3": 0.1}

        adapted_weights = realtime_adapter.adapt_weights(initial_weights, feedback)

        assert adapted_weights["feature1"] > initial_weights["feature1"]
        assert adapted_weights["feature2"] < initial_weights["feature2"]
        assert adapted_weights["feature3"] < initial_weights["feature3"]

    def test_network_adaptation(self, realtime_adapter):
        """Test dynamic weight network adaptation."""
        network = DynamicWeightNetwork(
            initial_weights={"node1": {"node2": 0.7, "node3": 0.3}, "node2": {"node1": 0.4, "node3": 0.6}}
        )

        # Simulate positive feedback for node1-node2 connection
        update = WeightUpdate(source="node1", target="node2", weight_change=0.2, feedback=0.9)

        network.apply_update(update)

        assert network.weights["node1"]["node2"] > 0.7
        assert network.weights["node2"]["node1"] < 0.4

    def test_adaptation_state_management(self, realtime_adapter):
        """Test adaptation state management."""
        initial_state = AdaptationState(weights={"feature1": 0.5, "feature2": 0.3}, feedback_history=[])

        # Apply adaptation
        adapted_state = realtime_adapter.adapt_state(initial_state, {"feature1": 0.7, "feature2": 0.2})

        assert adapted_state.weights["feature1"] > initial_state.weights["feature1"]
        assert adapted_state.weights["feature2"] < initial_state.weights["feature2"]
        assert len(adapted_state.feedback_history) == 1
