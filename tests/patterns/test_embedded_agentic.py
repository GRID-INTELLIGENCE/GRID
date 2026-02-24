"""Tests for embedded agentic pattern detection."""

import pytest

from grid.essence.core_state import EssentialState
from grid.patterns.embedded_agentic import EmbeddedAgenticDetector, ExtendedPatternRecognition


@pytest.mark.asyncio
async def test_detect_neural_network_pattern():
    """Test detection of neural network embedded agentic pattern."""
    state = EssentialState(
        pattern_signature="test_neural",
        quantum_state={
            "nodes": 100,
            "layers": 3,
            "weights": [0.5, 0.3, 0.2],
            "activation": "relu",
            "blended_val": 0.7,
        },
        context_depth=1.0,
        coherence_factor=0.8,
    )

    detector = EmbeddedAgenticDetector()
    result = await detector.detect_embedded_agentic(state)

    assert "embedded_agentic_species" in result
    assert "neural_network" in result["embedded_agentic_species"]
    assert result["confidence_scores"]["neural_network"] > 0.3


@pytest.mark.asyncio
async def test_detect_information_flow_pattern():
    """Test detection of information flow embedded agentic pattern."""
    state = EssentialState(
        pattern_signature="test_flow",
        quantum_state={
            "propagation": True,
            "influence": 0.8,
            "vector": [1.0, 0.5, 0.3],
            "pathway": "network",
            "flow": "active",
            "blended_val": 0.6,
        },
        context_depth=1.0,
        coherence_factor=0.7,
    )

    detector = EmbeddedAgenticDetector()
    result = await detector.detect_embedded_agentic(state)

    assert "embedded_agentic_species" in result
    assert "information_flow" in result["embedded_agentic_species"]
    assert result["confidence_scores"]["information_flow"] > 0.3


@pytest.mark.asyncio
async def test_extended_pattern_recognition():
    """Test extended pattern recognition with embedded agentic detection."""
    state = EssentialState(
        pattern_signature="test_extended",
        quantum_state={
            "nodes": 50,
            "edges": 100,
            "network": "graph",
            "blended_val": 0.5,
        },
        context_depth=1.0,
        coherence_factor=0.6,
    )

    recognizer = ExtendedPatternRecognition()
    patterns = await recognizer.recognize(state)

    # Should include base patterns
    assert len(patterns) > 0

    # Should detect embedded agentic patterns
    analysis = await recognizer.get_embedded_analysis(state)
    assert "embedded_agentic_species" in analysis
    assert len(analysis["embedded_agentic_species"]) > 0


@pytest.mark.asyncio
async def test_structure_analysis():
    """Test structure analysis for embedded agentic patterns."""
    state = EssentialState(
        pattern_signature="test_structure",
        quantum_state={
            "graph": {
                "nodes": ["A", "B", "C"],
                "edges": [("A", "B"), ("B", "C")],
            },
            "blended_val": 0.4,
        },
        context_depth=1.0,
        coherence_factor=0.5,
    )

    detector = EmbeddedAgenticDetector()
    result = await detector.detect_embedded_agentic(state)

    structure = result["structure_analysis"]
    assert structure["has_structure"] is True
    assert structure["has_connections"] is True
