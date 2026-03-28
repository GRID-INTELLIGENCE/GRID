"""Core state representation for GRID.

Minimal implementation to satisfy benchmark and intelligence tests.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any


@dataclass
class EssentialState:
    """Fundamental state container for the intelligence pipeline."""

    pattern_signature: str
    quantum_state: dict[str, Any]
    context_depth: float
    coherence_factor: float

    def _quantum_transform(self, context: Context, coherence_delta: float = 0.1) -> EssentialState:
        """Produce a transformed state influenced by context.

        Args:
            context: The context influencing the transformation.
            coherence_delta: Adjustment to coherence_factor. Positive values increase
                coherence (reinforcement), negative values decay it (degradation).
                Clamped to [0.0, 1.0].
        """
        new_signature = f"{self.pattern_signature}_ctx_{context.quantum_signature}"
        new_coherence = min(1.0, max(0.0, self.coherence_factor + coherence_delta))
        return replace(
            self,
            pattern_signature=new_signature,
            coherence_factor=new_coherence,
            context_depth=context.temporal_depth,
        )

    def decay(self, rate: float = 0.05) -> EssentialState:
        """Apply coherence decay — models natural degradation over time or inactivity.

        Args:
            rate: Decay amount subtracted from coherence_factor. Must be >= 0.
        """
        return replace(
            self,
            coherence_factor=max(0.0, self.coherence_factor - abs(rate)),
        )


# Local import to avoid circulars at module import time
from grid.awareness.context import Context  # noqa: E402  (late import for typing/logic)
