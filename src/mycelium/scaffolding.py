"""
Adaptive Scaffolding — Dynamic content adaptation for accessibility.

Directly extends GRID's ScaffoldingEngine and CognitiveRouter patterns.
Adjusts explanation depth, complexity, and format based on:
  - Detected cognitive load (from interaction patterns)
  - User expertise level (from persona)
  - Explicit feedback ("too complex" / "too simple")

The scaffolding is the bridge between raw synthesis output and what
the user actually receives. It transforms SynthesisResults into
outputs appropriate for the user's current state.

Like how a mother tree routes more nutrients to a stressed seedling,
the scaffolding routes more support to users who need it.

Inspired by:
  - GRID's ScaffoldingEngine (11 strategies, load-based selection)
  - GRID's CognitiveRouter (expertise thresholds, route scoring)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from mycelium.core import (
    ExpertiseLevel,
    Highlight,
    HighlightPriority,
    PersonaProfile,
    SynthesisResult,
)

logger = logging.getLogger(__name__)


class ScaffoldDepth(StrEnum):
    """Scaffolding depth. Maps to GRID's cognitive load thresholds."""

    NONE = "none"  # expert user, no scaffolding needed
    LIGHT = "light"  # examples only
    MODERATE = "moderate"  # examples + explanations + chunking
    FULL = "full"  # step-by-step + hints + progressive disclosure
    MAXIMUM = "maximum"  # all strategies + visual aids + audio cues


class Strategy(StrEnum):
    """Scaffolding strategies. Subset of GRID's 11 ScaffoldingStrategies."""

    CHUNKING = "chunking"  # break into digestible pieces
    SIMPLIFICATION = "simplification"  # reduce vocabulary complexity
    EXAMPLES = "examples"  # add concrete examples
    STEP_BY_STEP = "step_by_step"  # sequential walkthrough
    HIGHLIGHTING = "highlighting"  # emphasize key terms
    PROGRESSIVE = "progressive"  # reveal information gradually
    ANALOGY = "analogy"  # explain through comparison
    SUMMARY_FIRST = "summary_first"  # lead with the gist


@dataclass
class ScaffoldedOutput:
    """The final output after scaffolding has been applied."""

    # What the user sees
    content: str

    # Metadata about what was done
    depth_applied: ScaffoldDepth
    strategies_used: list[Strategy] = field(default_factory=list)
    cognitive_reduction: float = 0.0  # estimated load reduction (0.0–1.0)
    sections: list[dict[str, str]] = field(default_factory=list)  # named content blocks

    # Feedback hooks
    was_helpful: bool | None = None
    too_complex: bool | None = None
    too_simple: bool | None = None


class AdaptiveScaffold:
    """Wraps synthesis output in persona-appropriate scaffolding.

    The scaffold doesn't change what is said — it changes how it's
    presented. Same truth, different packaging.
    """

    # Strategy selection thresholds (inspired by GRID's CognitiveRouter)
    _DEPTH_STRATEGIES: dict[ScaffoldDepth, list[Strategy]] = {
        ScaffoldDepth.NONE: [],
        ScaffoldDepth.LIGHT: [
            Strategy.HIGHLIGHTING,
            Strategy.SUMMARY_FIRST,
        ],
        ScaffoldDepth.MODERATE: [
            Strategy.HIGHLIGHTING,
            Strategy.SUMMARY_FIRST,
            Strategy.CHUNKING,
            Strategy.EXAMPLES,
        ],
        ScaffoldDepth.FULL: [
            Strategy.HIGHLIGHTING,
            Strategy.SUMMARY_FIRST,
            Strategy.CHUNKING,
            Strategy.EXAMPLES,
            Strategy.STEP_BY_STEP,
            Strategy.ANALOGY,
        ],
        ScaffoldDepth.MAXIMUM: [
            Strategy.HIGHLIGHTING,
            Strategy.SUMMARY_FIRST,
            Strategy.CHUNKING,
            Strategy.SIMPLIFICATION,
            Strategy.EXAMPLES,
            Strategy.STEP_BY_STEP,
            Strategy.ANALOGY,
            Strategy.PROGRESSIVE,
        ],
    }

    def __init__(self, persona: PersonaProfile | None = None) -> None:
        self._persona = persona or PersonaProfile()
        self._feedback_history: list[dict[str, Any]] = []
        self._depth_override: ScaffoldDepth | None = None

    @property
    def persona(self) -> PersonaProfile:
        return self._persona

    @persona.setter
    def persona(self, value: PersonaProfile) -> None:
        self._persona = value

    def scaffold(
        self,
        result: SynthesisResult,
        depth: ScaffoldDepth | None = None,
    ) -> ScaffoldedOutput:
        """Apply scaffolding to a SynthesisResult.

        Args:
            result: Raw synthesis output to scaffold.
            depth: Override scaffolding depth. Auto-detected if None.

        Returns:
            ScaffoldedOutput ready for the user.
        """
        effective_depth = depth or self._depth_override or self._auto_detect_depth()
        strategies = self._DEPTH_STRATEGIES.get(effective_depth, [])

        sections: list[dict[str, str]] = []
        content_parts: list[str] = []

        # Apply strategies in order
        if Strategy.SUMMARY_FIRST in strategies:
            sections.append({"title": "In Brief", "content": result.gist})
            content_parts.append(f"IN BRIEF: {result.gist}")

        if Strategy.HIGHLIGHTING in strategies and result.highlights:
            kw_section = self._format_highlights(result.highlights)
            sections.append({"title": "Key Points", "content": kw_section})
            content_parts.append(f"\nKEY POINTS:\n{kw_section}")

        if Strategy.ANALOGY in strategies and result.analogy:
            sections.append({"title": "Think of It Like", "content": result.analogy})
            content_parts.append(f"\nTHINK OF IT LIKE: {result.analogy}")

        if Strategy.CHUNKING in strategies and result.summary:
            chunked = self._chunk_text(result.summary)
            sections.append({"title": "Summary", "content": chunked})
            content_parts.append(f"\nSUMMARY:\n{chunked}")

        if Strategy.STEP_BY_STEP in strategies and result.explanation:
            stepped = self._to_steps(result.explanation)
            sections.append({"title": "Step by Step", "content": stepped})
            content_parts.append(f"\nSTEP BY STEP:\n{stepped}")
        elif result.explanation and effective_depth != ScaffoldDepth.NONE:
            sections.append({"title": "Details", "content": result.explanation})
            content_parts.append(f"\nDETAILS: {result.explanation}")

        if Strategy.EXAMPLES in strategies:
            example = self._generate_example_hint(result)
            if example:
                sections.append({"title": "Example", "content": example})
                content_parts.append(f"\nEXAMPLE: {example}")

        # If no strategies were applied, just return the gist + summary
        if not content_parts:
            content_parts = [result.gist]
            if result.summary:
                content_parts.append(result.summary)

        # Estimate cognitive reduction
        reduction = len(strategies) * 0.1  # rough heuristic
        reduction = min(reduction, 0.8)

        content = "\n".join(content_parts)

        # Apply simplification AFTER content assembly so it affects final output
        if Strategy.SIMPLIFICATION in strategies:
            content = self._simplify_vocabulary(content)
            for i, section in enumerate(sections):
                sections[i]["content"] = self._simplify_vocabulary(
                    section["content"]
                )

        return ScaffoldedOutput(
            content=content,
            depth_applied=effective_depth,
            strategies_used=list(strategies),
            cognitive_reduction=reduction,
            sections=sections,
        )

    def feedback(
        self,
        too_complex: bool | None = None,
        too_simple: bool | None = None,
    ) -> ScaffoldDepth:
        """User feedback adjusts future scaffolding depth.

        Returns:
            The new effective scaffolding depth.
        """
        current = self._depth_override or self._auto_detect_depth()

        if too_complex:
            current = self._increase_depth(current)
            self._feedback_history.append({"type": "too_complex"})
        elif too_simple:
            current = self._decrease_depth(current)
            self._feedback_history.append({"type": "too_simple"})

        self._depth_override = current
        logger.info("AdaptiveScaffold: depth adjusted to %s", current.value)
        return current

    def reset_depth(self) -> None:
        """Clear depth override. Return to auto-detection."""
        self._depth_override = None
        self._feedback_history.clear()

    # --- Auto-detection ---

    def _auto_detect_depth(self) -> ScaffoldDepth:
        """Determine scaffolding depth from persona."""
        expertise = self._persona.expertise
        challenges = self._persona.challenges
        attention = self._persona.attention_span

        # Challenges always increase scaffolding
        if challenges:
            return ScaffoldDepth.MAXIMUM

        match expertise:
            case ExpertiseLevel.CHILD:
                return ScaffoldDepth.MAXIMUM
            case ExpertiseLevel.BEGINNER:
                return ScaffoldDepth.FULL
            case ExpertiseLevel.FAMILIAR:
                return ScaffoldDepth.MODERATE
            case ExpertiseLevel.PROFICIENT:
                return ScaffoldDepth.LIGHT
            case ExpertiseLevel.EXPERT:
                return ScaffoldDepth.NONE

        # Short attention span bumps up scaffolding
        if attention == "short":
            return ScaffoldDepth.FULL

        return ScaffoldDepth.MODERATE

    # --- Strategy implementations ---

    def _format_highlights(self, highlights: list[Highlight]) -> str:
        """Format highlights into a readable list."""
        lines: list[str] = []
        for h in highlights:
            priority_marker = {
                HighlightPriority.CRITICAL: "***",
                HighlightPriority.HIGH: "**",
                HighlightPriority.MEDIUM: "*",
                HighlightPriority.LOW: "",
            }.get(h.priority, "")

            if h.context:
                lines.append(f"  {priority_marker}{h.text}{priority_marker} — {h.context}")
            else:
                lines.append(f"  {priority_marker}{h.text}{priority_marker}")
        return "\n".join(lines)

    def _chunk_text(self, text: str, chunk_size: int = 80) -> str:
        """Break text into digestible paragraphs."""
        sentences = [s.strip() for s in text.split(". ") if s.strip()]
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for sentence in sentences:
            if not sentence.endswith("."):
                sentence += "."
            sent_len = len(sentence)

            if current_len + sent_len > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_len = sent_len
            else:
                current_chunk.append(sentence)
                current_len += sent_len

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return "\n\n".join(chunks)

    def _to_steps(self, text: str) -> str:
        """Convert explanation text into numbered steps."""
        sentences = [s.strip() for s in text.split(". ") if s.strip()]
        steps: list[str] = []
        for i, sentence in enumerate(sentences, 1):
            if not sentence.endswith("."):
                sentence += "."
            steps.append(f"  {i}. {sentence}")
        return "\n".join(steps)

    def _simplify_vocabulary(self, text: str) -> str:
        """Replace complex words with simpler alternatives."""
        replacements: dict[str, str] = {
            "utilize": "use",
            "implement": "build",
            "facilitate": "help",
            "leverage": "use",
            "paradigm": "pattern",
            "methodology": "method",
            "infrastructure": "system",
            "functionality": "feature",
            "configuration": "setup",
            "optimization": "improvement",
            "initialization": "start",
            "authentication": "login check",
            "authorization": "permission check",
            "comprehensive": "complete",
            "subsequently": "then",
            "furthermore": "also",
            "nevertheless": "but",
            "consequently": "so",
            "approximately": "about",
            "demonstrate": "show",
            "fundamental": "basic",
            "significant": "important",
            "instantiate": "create",
            "terminate": "stop",
            "propagate": "spread",
            "accumulate": "collect",
            "enumerate": "list",
        }

        result = text
        for complex_word, simple_word in replacements.items():
            # Case-insensitive replacement preserving sentence position
            import re

            pattern = re.compile(re.escape(complex_word), re.IGNORECASE)
            result = pattern.sub(simple_word, result)

        return result

    def _generate_example_hint(self, result: SynthesisResult) -> str:
        """Generate a brief example hint based on detected patterns."""
        if not result.highlights:
            return ""

        top_keyword = result.highlights[0].text if result.highlights else ""
        patterns = result.patterns_applied

        if "flow" in patterns:
            return f"Like water flowing through pipes — '{top_keyword}' is what moves through the system."
        if "repetition" in patterns:
            return f"Notice how '{top_keyword}' keeps coming up — that's the thread connecting everything."
        if "spatial" in patterns:
            return f"Think of '{top_keyword}' as the center of a map — everything else surrounds it."
        if "cause" in patterns:
            return f"'{top_keyword}' is the domino that starts the chain reaction here."

        return f"The main idea revolves around '{top_keyword}'."

    # --- Depth adjustment ---

    @staticmethod
    def _increase_depth(current: ScaffoldDepth) -> ScaffoldDepth:
        """More scaffolding (simpler output)."""
        order = list(ScaffoldDepth)
        idx = order.index(current)
        return order[min(idx + 1, len(order) - 1)]

    @staticmethod
    def _decrease_depth(current: ScaffoldDepth) -> ScaffoldDepth:
        """Less scaffolding (more raw output)."""
        order = list(ScaffoldDepth)
        idx = order.index(current)
        return order[max(idx - 1, 0)]
