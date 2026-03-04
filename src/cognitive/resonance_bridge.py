"""
Resonance Bridge — Event bus → Pattern Manager bridge.

Subscribes to pathways.resonance.* events and feeds them into
AdvancedPatternManager.learn_from_resonance() for temporally-aware
pattern learning.

Instead of binary "correct/incorrect" feedback, resonance signals carry
connection_strength, semantic_similarity, and emotional_amplification —
enabling gradient-based confidence adjustments.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from unified_fabric import Event, get_event_bus

if TYPE_CHECKING:
    from cognitive.pattern_manager import AdvancedPatternManager

logger = logging.getLogger(__name__)


class ResonanceBridge:
    """Bridge between Pathways resonance events and GRID pattern learning.

    Subscribes to pathways.resonance.* on the event bus and translates
    resonance signals into pattern learning updates.
    """

    def __init__(self, pattern_manager: AdvancedPatternManager) -> None:
        self._pattern_manager = pattern_manager
        self._event_bus = get_event_bus()
        self._initialized = False
        self._events_processed: int = 0

    async def initialize(self) -> None:
        """Subscribe to resonance events on the event bus."""
        if self._initialized:
            return

        self._event_bus.subscribe(
            "pathways.resonance.*",
            self._on_resonance_event,
            domain="pathways",
        )
        self._initialized = True
        logger.info("ResonanceBridge initialized — listening for pathways.resonance.*")

    async def _on_resonance_event(self, event: Event) -> None:
        """Handle a resonance event from the event bus.

        Extracts resonance features and feeds them into the pattern manager
        for gradient-based confidence adjustment.
        """
        payload = event.payload
        connection_strength = payload.get("connection_strength", 0.0)
        semantic_similarity = payload.get("semantic_similarity", 0.0)
        emotional_amplification = payload.get("emotional_amplification", 0.0)
        trigger_content = payload.get("trigger_content", "")
        resonating_content = payload.get("resonating_content", "")

        features: dict[str, Any] = {
            "connection_strength": connection_strength,
            "semantic_similarity": semantic_similarity,
            "emotional_amplification": emotional_amplification,
            "trigger_content": trigger_content,
            "resonating_content": resonating_content,
            "temporal_source": "pathways",
        }

        # Feed into all registered patterns — the manager decides relevance
        for pattern_id in list(self._pattern_manager._patterns):
            self._pattern_manager.learn_from_resonance(
                pattern_id=pattern_id,
                features=features,
                connection_strength=connection_strength,
                semantic_similarity=semantic_similarity,
                emotional_amplification=emotional_amplification,
            )

        self._events_processed += 1
        logger.info(
            "Resonance event processed: strength=%.2f similarity=%.2f amplification=%.2f",
            connection_strength,
            semantic_similarity,
            emotional_amplification,
        )

    @property
    def events_processed(self) -> int:
        """Number of resonance events processed."""
        return self._events_processed

    def get_stats(self) -> dict[str, Any]:
        """Get bridge statistics."""
        return {
            "initialized": self._initialized,
            "events_processed": self._events_processed,
            "pattern_count": len(self._pattern_manager._patterns),
        }
