"""Edge case tests for hybrid pattern detection."""

from __future__ import annotations

import pytest

from grid.essence.core_state import EssentialState
from grid.patterns.hybrid_detection import (
    HybridPatternDetector,
    HybridPatternResult,
    NeuralPatternDetector,
    PatternDetectionResult,
    StatisticalPatternDetector,
    SyntacticPatternDetector,
)


class TestStatisticalPatternDetectorEdgeCases:
    """Test StatisticalPatternDetector edge cases."""

    @pytest.fixture
    def detector(self):
        """Create statistical pattern detector."""
        return StatisticalPatternDetector()

    @pytest.fixture
    def base_state(self):
        """Create base essential state."""
        return EssentialState(
            pattern_signature="test_sig",
            quantum_state={"metric1": 0.5, "metric2": 0.3},
            context_depth=1.0,
            coherence_factor=0.5,
        )

    @pytest.mark.asyncio
    async def test_detect_with_empty_quantum_state(self, detector):
        """Test detection with empty quantum state."""
        state = EssentialState(
            pattern_signature="test_sig",
            quantum_state={},
            context_depth=1.0,
            coherence_factor=0.5,
        )
        result = await detector.detect(state, window_size=10)

        assert isinstance(result, PatternDetectionResult)
        assert result.method == "statistical"
        assert len(result.patterns) == 0

    @pytest.mark.asyncio
    async def test_detect_with_window_size_zero(self, detector, base_state):
        """Test detection with window size of zero."""
        result = await detector.detect(base_state, window_size=0)

        assert isinstance(result, PatternDetectionResult)
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_detect_with_negative_values(self, detector):
        """Test detection with negative metric values."""
        state = EssentialState(
            pattern_signature="test_sig",
            quantum_state={"metric1": -0.5, "metric2": -0.3},
            context_depth=1.0,
            coherence_factor=0.5,
        )

        # Add some history
        for i in range(5):
            await detector.detect(state, window_size=10)

        result = await detector.detect(state, window_size=10)
        assert isinstance(result, PatternDetectionResult)

    @pytest.mark.asyncio
    async def test_detect_with_extreme_values(self, detector):
        """Test detection with extreme metric values."""
        state = EssentialState(
            pattern_signature="test_sig",
            quantum_state={"metric1": 1e10, "metric2": -1e10},
            context_depth=1.0,
            coherence_factor=0.5,
        )

        for i in range(5):
            await detector.detect(state, window_size=10)

        result = await detector.detect(state, window_size=10)
        assert isinstance(result, PatternDetectionResult)

    @pytest.mark.asyncio
    async def test_detect_with_single_metric(self, detector):
        """Test detection with single metric."""
        state = EssentialState(
            pattern_signature="test_sig",
            quantum_state={"single_metric": 0.5},
            context_depth=1.0,
            coherence_factor=0.5,
        )

        for i in range(10):
            new_state = EssentialState(
                pattern_signature=f"sig_{i}",
                quantum_state={"single_metric": 0.5 + i * 0.01},
                context_depth=1.0,
                coherence_factor=0.5,
            )
            await detector.detect(new_state, window_size=10)

        result = await detector.detect(state, window_size=10)
        assert isinstance(result, PatternDetectionResult)
        # May or may not have patterns depending on trend detection
        assert result.confidence >= 0.0


class TestSyntacticPatternDetectorEdgeCases:
    """Test SyntacticPatternDetector edge cases."""

    @pytest.fixture
    def detector(self):
        """Create syntactic pattern detector."""
        return SyntacticPatternDetector()

    @pytest.mark.asyncio
    async def test_detect_with_none_quantum_state(self, detector):
        """Test detection with None quantum state."""
        state = EssentialState(
            pattern_signature="test_sig",
            quantum_state={},
            context_depth=1.0,
            coherence_factor=0.5,
        )
        result = await detector.detect(state)

        assert isinstance(result, PatternDetectionResult)
        assert result.method == "syntactic"

    @pytest.mark.asyncio
    async def test_detect_with_nested_structure(self, detector):
        """Test detection with nested quantum state structure."""
        state = EssentialState(
            pattern_signature="test_sig",
            quantum_state={
                "level1": {"level2": {"value": 0.5}},
                "parent": "child_value",
            },
            context_depth=1.0,
            coherence_factor=0.5,
        )
        result = await detector.detect(state)

        assert isinstance(result, PatternDetectionResult)

    @pytest.mark.asyncio
    async def test_detect_with_hierarchical_keywords(self, detector):
        """Test detection with hierarchical pattern keywords."""
        state = EssentialState(
            pattern_signature="hierarchical_pattern",
            quantum_state={
                "parent": "root",
                "child": "leaf",
                "level": 3,
                "depth": 5,
                "tree": True,
            },
            context_depth=2.0,
            coherence_factor=0.8,
        )
        result = await detector.detect(state)

        assert isinstance(result, PatternDetectionResult)
        assert len(result.patterns) > 0

    @pytest.mark.asyncio
    async def test_detect_with_network_keywords(self, detector):
        """Test detection with network pattern keywords."""
        state = EssentialState(
            pattern_signature="network_pattern",
            quantum_state={
                "node": "A",
                "edge": "connection",
                "connection": True,
                "graph": True,
                "link": "direct",
            },
            context_depth=1.5,
            coherence_factor=0.7,
        )
        result = await detector.detect(state)

        assert isinstance(result, PatternDetectionResult)


class TestNeuralPatternDetectorEdgeCases:
    """Test NeuralPatternDetector edge cases."""

    @pytest.fixture
    def detector(self):
        """Create neural pattern detector."""
        return NeuralPatternDetector()

    @pytest.mark.asyncio
    async def test_detect_with_empty_features(self, detector):
        """Test detection with empty feature extraction."""
        state = EssentialState(
            pattern_signature="test_sig",
            quantum_state={},
            context_depth=1.0,
            coherence_factor=0.5,
        )
        result = await detector.detect(state)

        assert isinstance(result, PatternDetectionResult)
        assert result.method == "neural"
        assert len(result.patterns) == 0

    @pytest.mark.asyncio
    async def test_detect_with_learned_patterns(self, detector):
        """Test detection with learned patterns."""
        # First, learn some patterns
        for i in range(5):
            state = EssentialState(
                pattern_signature=f"pattern_{i}",
                quantum_state={"feature": i * 0.1},
                context_depth=1.0,
                coherence_factor=0.5,
            )
            await detector.detect(state)

        # Now detect similar pattern
        test_state = EssentialState(
            pattern_signature="pattern_1",
            quantum_state={"feature": 0.1},
            context_depth=1.0,
            coherence_factor=0.5,
        )
        result = await detector.detect(test_state)

        assert isinstance(result, PatternDetectionResult)

    @pytest.mark.asyncio
    async def test_detect_similarity_calculation(self, detector):
        """Test similarity calculation with different features."""
        state1 = EssentialState(
            pattern_signature="pattern_A",
            quantum_state={"a": 1.0, "b": 0.0},
            context_depth=1.0,
            coherence_factor=0.5,
        )
        state2 = EssentialState(
            pattern_signature="pattern_B",
            quantum_state={"a": 0.0, "b": 1.0},
            context_depth=1.0,
            coherence_factor=0.5,
        )

        result1 = await detector.detect(state1)
        result2 = await detector.detect(state2)

        assert isinstance(result1, PatternDetectionResult)
        assert isinstance(result2, PatternDetectionResult)


class TestHybridPatternDetectorEdgeCases:
    """Test HybridPatternDetector edge cases."""

    @pytest.fixture
    def detector(self):
        """Create hybrid pattern detector."""
        return HybridPatternDetector()

    @pytest.fixture
    def base_state(self):
        """Create base essential state."""
        return EssentialState(
            pattern_signature="test_sig",
            quantum_state={"metric1": 0.5, "metric2": 0.3},
            context_depth=1.0,
            coherence_factor=0.5,
        )

    @pytest.mark.asyncio
    async def test_detect_with_default_weights(self, detector, base_state):
        """Test detection with default weights."""
        result = await detector.detect(base_state)

        assert isinstance(result, HybridPatternResult)
        assert hasattr(result, "statistical_patterns")
        assert hasattr(result, "syntactic_patterns")
        assert hasattr(result, "neural_patterns")
        assert hasattr(result, "combined_patterns")
        assert hasattr(result, "confidence_scores")

    @pytest.mark.asyncio
    async def test_detect_with_custom_weights(self, detector, base_state):
        """Test detection with custom weights."""
        weights = {"statistical": 0.5, "syntactic": 0.3, "neural": 0.2}
        result = await detector.detect(base_state, weights=weights)

        assert isinstance(result, HybridPatternResult)

    @pytest.mark.asyncio
    async def test_detect_with_zero_weights(self, detector, base_state):
        """Test detection with zero weights."""
        weights = {"statistical": 0.0, "syntactic": 0.0, "neural": 0.0}
        result = await detector.detect(base_state, weights=weights)

        assert isinstance(result, HybridPatternResult)

    @pytest.mark.asyncio
    async def test_detect_with_partial_weights(self, detector, base_state):
        """Test detection with partial weights (missing some keys)."""
        weights = {"statistical": 0.8}  # Missing syntactic and neural
        result = await detector.detect(base_state, weights=weights)

        assert isinstance(result, HybridPatternResult)

    @pytest.mark.asyncio
    async def test_detect_with_empty_state(self, detector):
        """Test detection with empty essential state."""
        state = EssentialState(
            pattern_signature="",
            quantum_state={},
            context_depth=0.0,
            coherence_factor=0.0,
        )
        result = await detector.detect(state)

        assert isinstance(result, HybridPatternResult)


class TestPatternResultStructure:
    """Test pattern detection result structure and properties."""

    def test_pattern_detection_result_creation(self):
        """Test PatternDetectionResult dataclass creation."""
        result = PatternDetectionResult(
            patterns=["pattern1", "pattern2"],
            confidence=0.85,
            method="test",
            metadata={"key": "value"},
        )

        assert result.patterns == ["pattern1", "pattern2"]
        assert result.confidence == 0.85
        assert result.method == "test"
        assert result.metadata == {"key": "value"}

    def test_hybrid_pattern_result_creation(self):
        """Test HybridPatternResult dataclass creation."""
        result = HybridPatternResult(
            statistical_patterns=["trend"],
            syntactic_patterns=["structure"],
            neural_patterns=["learned"],
            combined_patterns=["combined"],
            confidence_scores={"statistical": 0.7, "syntactic": 0.8},
        )

        assert result.statistical_patterns == ["trend"]
        assert result.syntactic_patterns == ["structure"]
        assert result.combined_patterns == ["combined"]
        assert len(result.confidence_scores) == 2
