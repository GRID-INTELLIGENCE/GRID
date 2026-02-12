"""Pattern recognition for GRID (fast threshold path)."""

from __future__ import annotations

import numpy as np

from grid.essence.core_state import EssentialState


class PatternRecognition:
    """Fast heuristic recognizer (no ML) for sub-0.1ms SLA."""

    def __init__(self):
        self.quantum_field = np.zeros((64, 64))
        self.resonance_patterns: list[str] = []

    async def recognize(self, state: EssentialState) -> list[str]:
        blended = float(state.quantum_state.get("blended_val", 0.0))
        pattern = "strong-activation" if blended > 0.5 else "weak-activation"
        self.resonance_patterns.append(pattern)
        self.resonance_patterns = self.resonance_patterns[-5:]
        return self.resonance_patterns.copy()
