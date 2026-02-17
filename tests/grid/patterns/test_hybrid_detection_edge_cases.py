"""Edge case tests for hybrid pattern detection."""

from __future__ import annotations

import pytest

from grid.essence.core_state import EssentialState
from grid.patterns.hybrid_detection import (
    HybridPatternDetector,
    NeuralPatternDetector,
    PatternDetectionResult,
    StatisticalPatternDetector,
    SyntacticPatternDetector,
)


class TestStatisticalDetectorEdgeCases:
    """Edge case tests for statistical detector."""

    @pytest.mark.asyncio
    async def test_extract_metrics_ignores_non_numeric(self) -> None:
        """Non-numeric metric values should be ignored."""
        detector = StatisticalPatternDetector()
        state = EssentialState(
            pattern_signature="test",
            quantum_state={"metric": {"value": "bad"}, "valid": 1},
            context_depth=1.0,
            coherence_factor=0.5,
        )

        result = await detector.detect(state, window_size=2)

        assert isinstance(result, PatternDetectionResult)
        assert detector.history[-1]["valid"] == 1.0
        assert "metric" not in detector.history[-1]

    @pytest.mark.asyncio
    async def test_detect_with_empty_quantum_state(self) -> None:
        """Empty quantum state should not raise errors."""
        detector = StatisticalPatternDetector()
        state = EssentialState(
            pattern_signature="test",
            quantum_state={},
            context_depth=0.5,
            coherence_factor=0.3,
        )

        result = await detector.detect(state, window_size=2)

        assert result.patterns == []
        assert result.confidence == 0.0


class TestSyntacticDetectorComplexPatterns:
    """Complex pattern tests for syntactic detector."""

    @pytest.mark.asyncio
    async def test_detect_relational_web_patterns(self) -> None:
        """Relational web should produce syntactic patterns."""
        detector = SyntacticPatternDetector()
        state = EssentialState(
            pattern_signature="test",
            quantum_state={"nodes": ["A", "B"], "edges": [("A", "B")]},
            context_depth=1.0,
            coherence_factor=0.6,
        )
        state.relational_web = {"parent": "A", "child": "B", "link": "A-B", "node": "A"}

        result = await detector.detect(state)

        assert any("SYNTACTIC_" in pattern for pattern in result.patterns)


class TestNeuralDetectorLearning:
    """Tests for neural detector learning behavior."""

    @pytest.mark.asyncio
    async def test_neural_detector_learns_and_matches(self) -> None:
        """Neural detector should learn and later match patterns."""
        detector = NeuralPatternDetector()
        state = EssentialState(
            pattern_signature="test",
            quantum_state={"nodes": 3, "edges": 2},
            context_depth=1.0,
            coherence_factor=0.8,
        )

        initial = await detector.detect(state)
        assert initial.patterns == []
        assert detector.learned_patterns

        followup = await detector.detect(state)

        assert any(pattern.startswith("NEURAL_PATTERN") for pattern in followup.patterns)


class TestHybridDetectorIntegration:
    """Integration test for hybrid detector weights."""

    @pytest.mark.asyncio
    async def test_hybrid_detector_weighted_confidence(self) -> None:
        """Hybrid detector should honor provided weights."""
        detector = HybridPatternDetector()
        state = EssentialState(
            pattern_signature="test",
            quantum_state={"nodes": [1, 2, 3], "edges": [(1, 2), (2, 3)], "sequence": [1, 2, 3]},
            context_depth=1.0,
            coherence_factor=0.85,
        )

        await detector.detect(state)
        result = await detector.detect(state, weights={"statistical": 0.2, "syntactic": 0.3, "neural": 0.5})

        assert result.metadata["weights"] == {"statistical": 0.2, "syntactic": 0.3, "neural": 0.5}
        assert set(result.combined_patterns) >= set(result.syntactic_patterns + result.neural_patterns)
