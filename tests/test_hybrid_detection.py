"""Tests for hybrid pattern detection functionality."""

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


class TestStatisticalPatternDetector:
    """Test StatisticalPatternDetector."""

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
    async def test_detect_with_insufficient_history(self, detector, base_state):
        """Test detection with insufficient history."""
        result = await detector.detect(base_state, window_size=10)

        assert isinstance(result, PatternDetectionResult)
        assert result.method == "statistical"
        assert len(result.patterns) == 0  # No history yet
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_detect_trends(self, detector, base_state):
        """Test trend detection."""
        # Create states with increasing metrics
        for i in range(15):
            state = EssentialState(
                pattern_signature=f"sig_{i}",
                quantum_state={"metric1": 0.5 + i * 0.01, "metric2": 0.3 - i * 0.005},
                context_depth=1.0 + i * 0.1,
                coherence_factor=0.5 + i * 0.02,
            )
            await detector.detect(state, window_size=10)

        result = await detector.detect(base_state, window_size=10)

        # Should detect trends
        assert len(result.patterns) > 0
        assert any("INCREASING" in p for p in result.patterns)
        assert result.confidence > 0.0

    @pytest.mark.asyncio
    async def test_detect_distribution_changes(self, detector, base_state):
        """Test distribution change detection."""
        # Create states with stable metrics, then change
        for i in range(10):
            state = EssentialState(
                pattern_signature=f"sig_{i}",
                quantum_state={"metric1": 0.5, "metric2": 0.3},
                context_depth=1.0,
                coherence_factor=0.5,
            )
            await detector.detect(state, window_size=5)

        # Now change distribution
        for i in range(10, 20):
            state = EssentialState(
                pattern_signature=f"sig_{i}",
                quantum_state={"metric1": 0.8, "metric2": 0.6},
                context_depth=1.0,
                coherence_factor=0.7,
            )
            await detector.detect(state, window_size=5)

        result = await detector.detect(base_state, window_size=5)

        # Should detect distribution changes
        assert len(result.patterns) > 0
        assert any("DISTRIBUTION_SHIFT" in p or "VARIANCE_CHANGE" in p for p in result.patterns)


class TestSyntacticPatternDetector:
    """Test SyntacticPatternDetector."""

    @pytest.fixture
    def detector(self):
        """Create syntactic pattern detector."""
        return SyntacticPatternDetector()

    @pytest.mark.asyncio
    async def test_detect_hierarchical_pattern(self, detector):
        """Test detecting hierarchical patterns."""
        state = EssentialState(
            pattern_signature="test",
            quantum_state={
                "parent": {"child": {"grandchild": {}}},
                "level": 3,
                "depth": 2,
            },
            context_depth=1.0,
            coherence_factor=0.5,
        )

        result = await detector.detect(state)

        assert isinstance(result, PatternDetectionResult)
        assert result.method == "syntactic"
        assert any("HIERARCHICAL" in p for p in result.patterns)

    @pytest.mark.asyncio
    async def test_detect_network_pattern(self, detector):
        """Test detecting network patterns."""
        state = EssentialState(
            pattern_signature="test",
            quantum_state={
                "nodes": [1, 2, 3, 4, 5],
                "edges": [(1, 2), (2, 3), (3, 4)],
                "graph": {"type": "network"},
            },
            context_depth=1.0,
            coherence_factor=0.5,
        )

        result = await detector.detect(state)

        assert any("NETWORK" in p for p in result.patterns)

    @pytest.mark.asyncio
    async def test_detect_sequential_pattern(self, detector):
        """Test detecting sequential patterns."""
        state = EssentialState(
            pattern_signature="test",
            quantum_state={
                "sequence": [1, 2, 3, 4],
                "order": "ascending",
                "step": 1,
            },
            context_depth=1.0,
            coherence_factor=0.5,
        )

        result = await detector.detect(state)

        assert any("SEQUENTIAL" in p for p in result.patterns)


class TestNeuralPatternDetector:
    """Test NeuralPatternDetector."""

    @pytest.fixture
    def detector(self):
        """Create neural pattern detector."""
        return NeuralPatternDetector()

    @pytest.mark.asyncio
    async def test_detect_and_learn(self, detector):
        """Test pattern detection and learning."""
        state = EssentialState(
            pattern_signature="test",
            quantum_state={"metric1": 0.5, "metric2": 0.3},
            context_depth=1.0,
            coherence_factor=0.8,  # High coherence for learning
        )

        result = await detector.detect(state)

        assert isinstance(result, PatternDetectionResult)
        assert result.method == "neural"
        # Should learn pattern with high coherence
        assert len(detector.learned_patterns) > 0

    @pytest.mark.asyncio
    async def test_pattern_matching(self, detector):
        """Test pattern matching."""
        # Learn a pattern first
        state1 = EssentialState(
            pattern_signature="test1",
            quantum_state={"metric1": 0.5, "metric2": 0.3},
            context_depth=1.0,
            coherence_factor=0.8,
        )
        await detector.detect(state1)

        # Similar state should match
        state2 = EssentialState(
            pattern_signature="test2",
            quantum_state={"metric1": 0.52, "metric2": 0.31},
            context_depth=1.0,
            coherence_factor=0.8,
        )
        result = await detector.detect(state2)

        # Should match learned pattern
        assert len(result.patterns) > 0
        assert any("NEURAL" in p for p in result.patterns)


class TestHybridPatternDetector:
    """Test HybridPatternDetector."""

    @pytest.fixture
    def detector(self):
        """Create hybrid pattern detector."""
        return HybridPatternDetector()

    @pytest.fixture
    def base_state(self):
        """Create base essential state."""
        return EssentialState(
            pattern_signature="test_sig",
            quantum_state={"metric1": 0.5, "metric2": 0.3, "nodes": [1, 2, 3]},
            context_depth=1.0,
            coherence_factor=0.7,
        )

    @pytest.mark.asyncio
    async def test_hybrid_detection(self, detector, base_state):
        """Test hybrid pattern detection."""
        result = await detector.detect(base_state)

        assert isinstance(result, HybridPatternResult)
        assert len(result.statistical_patterns) >= 0
        assert len(result.syntactic_patterns) >= 0
        assert len(result.neural_patterns) >= 0
        assert len(result.combined_patterns) >= 0
        assert "statistical" in result.confidence_scores
        assert "syntactic" in result.confidence_scores
        assert "neural" in result.confidence_scores

    @pytest.mark.asyncio
    async def test_custom_weights(self, detector, base_state):
        """Test detection with custom weights."""
        weights = {"statistical": 0.5, "syntactic": 0.3, "neural": 0.2}
        result = await detector.detect(base_state, weights=weights)

        assert result.metadata["weights"] == weights

    @pytest.mark.asyncio
    async def test_combined_patterns(self, detector, base_state):
        """Test that combined patterns include all methods."""
        # Build history for statistical detection
        for i in range(15):
            state = EssentialState(
                pattern_signature=f"sig_{i}",
                quantum_state={
                    "metric1": 0.5 + i * 0.01,
                    "nodes": [1, 2, 3],
                    "graph": {"type": "network"},
                },
                context_depth=1.0 + i * 0.1,
                coherence_factor=0.7,
            )
            await detector.detect(state)

        result = await detector.detect(base_state)

        # Should have patterns from multiple methods
        assert len(result.combined_patterns) > 0
        # Combined should be union of all methods
        all_method_patterns = set(result.statistical_patterns)
        all_method_patterns.update(result.syntactic_patterns)
        all_method_patterns.update(result.neural_patterns)
        assert set(result.combined_patterns) == all_method_patterns
