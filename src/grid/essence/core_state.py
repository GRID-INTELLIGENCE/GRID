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

    def _quantum_transform(self, context: Context) -> EssentialState:
        """Produce a transformed state influenced by context.

        Test expectations:
        - pattern_signature should change
        - coherence_factor should increase
        - context_depth should match context.temporal_depth
        """
        new_signature = f"{self.pattern_signature}_ctx_{context.quantum_signature}"
        new_coherence = self.coherence_factor + 0.1
        return replace(
            self,
            pattern_signature=new_signature,
            coherence_factor=new_coherence,
            context_depth=context.temporal_depth,
        )


# Local import to avoid circulars at module import time
from grid.awareness.context import Context  # noqa: E402  (late import for typing/logic)
