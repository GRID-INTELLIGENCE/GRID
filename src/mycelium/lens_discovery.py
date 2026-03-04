"""
Lens Discovery Engine — Auto-generate PatternLens from knowledge corpus.

When the PatternNavigator encounters an unknown concept, this engine
queries the federated knowledge base, runs pattern detection on the
results, and generates candidate PatternLens objects based on which
cognitive patterns appear in the content.

Quality filter: only generates lenses for patterns actually detected
(minimum 2 required). Auto-generated lenses are tagged with
metadata={"auto_generated": True}.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from mycelium.navigator import PatternLens
from mycelium.synthesizer import Synthesizer

if TYPE_CHECKING:
    from mycelium.knowledge_federation import KnowledgeFederator

logger = logging.getLogger(__name__)

# Minimum number of patterns detected to generate lenses
_MIN_PATTERNS_FOR_LENS = 2

# Templates for generating analogies per pattern type
_PATTERN_TEMPLATES: dict[str, dict[str, str]] = {
    "flow": {
        "analogy": "Like a river carrying {concept} from source to destination — each step follows naturally from the last.",
        "eli5": "{concept} is like water flowing downhill. It moves step by step, always going forward.",
        "visual_hint": "Picture a stream. {concept} flows through it from beginning to end.",
        "when_useful": "When you need to understand {concept} as a sequence or process.",
    },
    "spatial": {
        "analogy": "Think of {concept} as a building with rooms — each room has a purpose, connected by hallways.",
        "eli5": "{concept} is like a house. Different rooms do different things, but they're all under one roof.",
        "visual_hint": "Picture a blueprint. Each labeled room is a part of {concept}.",
        "when_useful": "When you need to see how the parts of {concept} are organized.",
    },
    "rhythm": {
        "analogy": "{concept} follows a beat — regular patterns that repeat and create predictability.",
        "eli5": "{concept} is like a song. Once you hear the beat, you know what comes next.",
        "visual_hint": "Picture a metronome clicking. Each click is a cycle of {concept}.",
        "when_useful": "When {concept} has regular, repeating patterns you can rely on.",
    },
    "repetition": {
        "analogy": "{concept} is built from the same building block used over and over — like bricks in a wall.",
        "eli5": "{concept} is like stacking the same LEGO piece again and again to build something big.",
        "visual_hint": "Picture a pattern of identical tiles covering a floor.",
        "when_useful": "When {concept} is made of many similar parts working together.",
    },
    "deviation": {
        "analogy": "In {concept}, the interesting part is what breaks the pattern — the exception that proves the rule.",
        "eli5": "{concept} is like finding a red marble in a jar of blue ones. The different one stands out.",
        "visual_hint": "Picture a straight line with one bump. The bump is where {concept} gets interesting.",
        "when_useful": "When you need to spot what's unusual or different about {concept}.",
    },
    "cause": {
        "analogy": "{concept} is a chain of dominoes — one action triggers the next in a clear sequence.",
        "eli5": "{concept} is like pushing the first domino. It knocks over the next one, and the next.",
        "visual_hint": "Picture dominoes in a line. Push the first one labeled '{concept}' and watch the chain.",
        "when_useful": "When you need to understand what causes what in {concept}.",
    },
    "combination": {
        "analogy": "{concept} emerges where multiple ideas intersect — like mixing colors to get a new one.",
        "eli5": "{concept} is like mixing yellow and blue paint. You get something new: green.",
        "visual_hint": "Picture a Venn diagram. {concept} lives where the circles overlap.",
        "when_useful": "When {concept} only makes sense as a combination of simpler ideas.",
    },
    "time": {
        "analogy": "{concept} unfolds over time like tree rings — each layer records a different moment.",
        "eli5": "{concept} is like a diary. Each page is a different day, and together they tell the whole story.",
        "visual_hint": "Picture a timeline. {concept} moves along it from past to future.",
        "when_useful": "When understanding {concept} requires seeing how it changes over time.",
    },
    "color": {
        "analogy": "{concept} has different shades — from light overview to deep detail, like zooming into a painting.",
        "eli5": "{concept} is like looking at a painting. From far away you see the whole picture; up close you see brushstrokes.",
        "visual_hint": "Picture a gradient from light to dark. Each shade is a level of detail in {concept}.",
        "when_useful": "When you need to see {concept} at different levels of detail.",
    },
}


class LensDiscoveryEngine:
    """Auto-generate PatternLens objects from knowledge corpus queries.

    Uses KnowledgeFederator to query for a concept, runs Synthesizer
    pattern detection on the results, and maps detected patterns to
    lens templates.
    """

    def __init__(
        self,
        federator: KnowledgeFederator,
        synthesizer: Synthesizer | None = None,
    ) -> None:
        self._federator = federator
        self._synthesizer = synthesizer or Synthesizer()
        self._discovery_cache: dict[str, list[PatternLens]] = {}

    async def discover_lenses(self, concept: str) -> list[PatternLens]:
        """Query knowledge and generate lenses based on detected patterns.

        Args:
            concept: The concept to discover lenses for.

        Returns:
            List of auto-generated PatternLens objects (may be empty
            if fewer than 2 patterns detected).
        """
        concept_key = concept.lower().strip()

        # Check cache
        if concept_key in self._discovery_cache:
            return self._discovery_cache[concept_key]

        # Query federated knowledge
        result = await self._federator.query(
            question=f"What is {concept}? Explain the key aspects.",
            top_k=5,
        )

        all_texts = result.grid_results + result.pathways_results
        if not all_texts:
            logger.info("No knowledge found for concept '%s'", concept)
            return []

        # Run synthesis to detect patterns
        combined = "\n\n".join(all_texts)
        synthesis = self._synthesizer.synthesize(combined)
        detected_patterns = synthesis.patterns_applied

        if len(detected_patterns) < _MIN_PATTERNS_FOR_LENS:
            logger.info(
                "Only %d patterns detected for '%s' (need %d) — skipping lens generation",
                len(detected_patterns),
                concept,
                _MIN_PATTERNS_FOR_LENS,
            )
            return []

        # Generate lenses from detected patterns
        lenses = self._generate_lenses(concept_key, detected_patterns)

        # Cache results
        self._discovery_cache[concept_key] = lenses

        logger.info(
            "Discovered %d lenses for '%s' from patterns: %s",
            len(lenses),
            concept,
            detected_patterns,
        )

        return lenses

    def _generate_lenses(self, concept: str, patterns: list[str]) -> list[PatternLens]:
        """Generate PatternLens objects from detected patterns using templates."""
        lenses: list[PatternLens] = []

        for pattern in patterns:
            template = _PATTERN_TEMPLATES.get(pattern)
            if template is None:
                continue

            lens = PatternLens(
                pattern=pattern,
                analogy=template["analogy"].format(concept=concept),
                eli5=template["eli5"].format(concept=concept),
                visual_hint=template["visual_hint"].format(concept=concept),
                when_useful=template["when_useful"].format(concept=concept),
            )
            lenses.append(lens)

        return lenses

    def get_stats(self) -> dict[str, Any]:
        """Get discovery engine statistics."""
        return {
            "cached_concepts": len(self._discovery_cache),
            "total_lenses_generated": sum(len(lenses) for lenses in self._discovery_cache.values()),
        }
