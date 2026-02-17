"""Complex scenario tests for embedded agentic detection."""

from __future__ import annotations

import pytest

from grid.essence.core_state import EssentialState
from grid.patterns.embedded_agentic import EmbeddedAgenticDetector, ExtendedPatternRecognition


class TestEmbeddedAgenticComplexSpecies:
    """Complex embedded agentic species detection tests."""

    @pytest.mark.asyncio
    async def test_detect_multiple_species(self) -> None:
        """Detector should identify multiple embedded species."""
        state = EssentialState(
            pattern_signature="complex",
            quantum_state={
                "nodes": 100,
                "layers": 3,
                "weights": [0.1, 0.2],
                "propagation": True,
                "flow": "active",
            },
            context_depth=1.2,
            coherence_factor=0.7,
        )
        detector = EmbeddedAgenticDetector()

        result = await detector.detect_embedded_agentic(state)

        species = result["embedded_agentic_species"]
        assert "neural_network" in species
        assert "information_flow" in species

    @pytest.mark.asyncio
    async def test_structure_analysis_nested_graph(self) -> None:
        """Nested graph structures should be detected."""
        state = EssentialState(
            pattern_signature="graph",
            quantum_state={"graph": {"nodes": ["A"], "edges": [("A", "B")]}, "blended_val": 0.5},
            context_depth=0.9,
            coherence_factor=0.6,
        )
        detector = EmbeddedAgenticDetector()

        result = await detector.detect_embedded_agentic(state)

        analysis = result["structure_analysis"]
        assert analysis["has_structure"] is True
        assert analysis["has_connections"] is True


class TestExtendedPatternRecognitionIntegration:
    """Integration tests for extended pattern recognition."""

    @pytest.mark.asyncio
    async def test_embedded_patterns_stored(self) -> None:
        """Embedded patterns should be stored on recognizer."""
        state = EssentialState(
            pattern_signature="test",
            quantum_state={"network": "graph", "edges": [(1, 2)]},
            context_depth=0.8,
            coherence_factor=0.6,
        )
        recognizer = ExtendedPatternRecognition()

        await recognizer.recognize(state)

        assert recognizer.embedded_patterns
