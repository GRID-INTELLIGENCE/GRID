"""Integration tests for pattern modules."""

from __future__ import annotations

import pytest

from grid.essence.core_state import EssentialState
from grid.patterns.embedded_agentic import ExtendedPatternRecognition
from grid.patterns.hybrid_detection import HybridPatternDetector


@pytest.mark.asyncio
async def test_patterns_integration_flow() -> None:
    """Hybrid and embedded agentic detectors should both return patterns."""
    state = EssentialState(
        pattern_signature="integration",
        quantum_state={
            "nodes": [1, 2, 3],
            "edges": [(1, 2), (2, 3)],
            "sequence": [1, 2, 3],
            "flow": "active",
        },
        context_depth=1.1,
        coherence_factor=0.85,
    )

    hybrid_detector = HybridPatternDetector()
    embedded_recognizer = ExtendedPatternRecognition()

    await hybrid_detector.detect(state)
    hybrid_result = await hybrid_detector.detect(state)
    embedded_patterns = await embedded_recognizer.recognize(state)

    assert hybrid_result.combined_patterns
    assert embedded_patterns
