"""
Instrument — The user-facing entry point for Mycelium.

This is what users interact with. One class. Simple methods.
Everything else (persona, synthesizer, navigator, scaffolding, sensory)
is wired together behind this single interface.

Design philosophy:
  - 3 verbs: synthesize, explore, simplify
  - 1 feedback loop: "did this click?"
  - Organic engagement: the tool adapts, not the user
  - Zero config to start, full control when wanted

Usage:
    from mycelium import Instrument

    m = Instrument()
    result = m.synthesize("Your complex document text here...")
    print(result.gist)          # one-line essence
    print(result.highlights)    # key points
    print(result.summary)       # short summary
    print(result.explanation)   # accessible explanation

    # Explore a concept through pattern lenses
    nav = m.explore("cache")
    print(nav.lens.eli5)        # "A shelf next to you with stuff you use a lot."

    # Didn't click? Try another lens
    nav2 = m.try_different("cache")

    # Adapt to the user
    m.set_user(expertise="beginner", tone="playful")

    # Give feedback
    m.feedback(too_complex=True)  # → scaffolding increases
"""

from __future__ import annotations

import logging
from typing import Any

from mycelium.core import (
    Depth,
    PersonaProfile,
    ResonanceLevel,
    SynthesisResult,
)
from mycelium.navigator import NavigationResult, PatternLens, PatternNavigator
from mycelium.persona import InteractionSignal, PersonaEngine
from mycelium.safety import (
    MAX_HIGHLIGHTS,
    MAX_REGISTERED_CONCEPTS,
    MAX_TRAIT_VALUE_LENGTH,
    SafetyGuard,
    SafetyVerdict,
)
from mycelium.scaffolding import AdaptiveScaffold, ScaffoldedOutput
from mycelium.sensory import SensoryMode, SensoryProfile
from mycelium.synthesizer import Synthesizer

logger = logging.getLogger(__name__)


class Instrument:
    """Mycelium Instrument — pattern recognition and synthesis, made simple.

    The single entry point for all Mycelium functionality.
    Wires together: persona detection, text synthesis, pattern navigation,
    adaptive scaffolding, and sensory formatting.

    Three missions:
      1. Understand the user → PersonaEngine
      2. Extract what matters → Synthesizer
      3. Make knowledge accessible → Navigator + Scaffold + Sensory
    """

    def __init__(
        self,
        depth: Depth | None = None,
        sensory_profile: SensoryProfile = SensoryProfile.DEFAULT,
    ) -> None:
        """Initialize the Instrument. Zero config required.

        Args:
            depth: Override synthesis depth. Auto-detected from persona if None.
            sensory_profile: Accessibility profile for output formatting.
        """
        self._safety = SafetyGuard()
        self._persona_engine = PersonaEngine()
        self._synthesizer = Synthesizer(self._persona_engine.profile)
        self._navigator = PatternNavigator(self._persona_engine.profile)
        self._scaffold = AdaptiveScaffold(self._persona_engine.profile)
        self._sensory = SensoryMode(sensory_profile)
        self._depth_override = depth

        logger.info("Mycelium Instrument initialized (sensory=%s)", sensory_profile.value)

    # ------------------------------------------------------------------
    # Mission 2: Extract what matters
    # ------------------------------------------------------------------

    def synthesize(
        self,
        text: str,
        depth: Depth | None = None,
        max_highlights: int = 10,
        scaffold: bool = True,
        format_output: bool = True,
    ) -> SynthesisResult:
        """Synthesize complex text into accessible output.

        This is the main method. Give it text, get back a gist,
        highlights, summary, explanation, and analogy — all adapted
        to the user's persona and sensory profile.

        Args:
            text: The source text (document, article, data, etc.).
            depth: Override depth (espresso/americano/cold_brew).
            max_highlights: Maximum keywords to extract.
            scaffold: Whether to apply adaptive scaffolding.
            format_output: Whether to apply sensory formatting.

        Returns:
            SynthesisResult with all layers of synthesis.
        """
        # Safety: validate input
        report = self._safety.validate_input(text)
        if not report.is_safe:
            logger.warning("Instrument.synthesize: input rejected: %s", report.reasons)
            return SynthesisResult(
                gist="(input could not be processed)",
                source_length=len(text) if isinstance(text, str) else 0,
            )
        text = report.sanitized_text or text

        # Safety: clamp max_highlights
        max_highlights = max(1, min(max_highlights, MAX_HIGHLIGHTS))

        # Record this as a persona signal
        self._persona_engine.observe(
            InteractionSignal(signal_type="query", content=text[:200])
        )

        # Sync persona across components
        self._sync_persona()

        effective_depth = depth or self._depth_override

        # 1. Core synthesis
        result = self._synthesizer.synthesize(
            text, depth=effective_depth, max_highlights=max_highlights
        )

        # 2. Apply scaffolding
        if scaffold:
            scaffolded = self._scaffold.scaffold(result)
            # Merge scaffolded content back into result
            result.explanation = scaffolded.content
            result.scaffolding_applied = [s.value for s in scaffolded.strategies_used]

        # 3. Apply sensory formatting
        if format_output:
            result.gist = self._sensory.format_output(result.gist)
            result.summary = self._sensory.format_output(result.summary)
            result.explanation = self._sensory.format_output(result.explanation)
            if result.analogy:
                result.analogy = self._sensory.format_output(result.analogy)

        return result

    def summarize(self, text: str, sentences: int = 3) -> str:
        """Quick summarization. Returns N most important sentences."""
        report = self._safety.validate_input(text)
        if not report.is_safe:
            return "(input could not be processed)"
        text = report.sanitized_text or text
        sentences = max(1, min(sentences, 20))
        self._sync_persona()
        raw = self._synthesizer.summarize(text, sentence_count=sentences)
        return self._sensory.format_output(raw)

    def simplify(self, text: str) -> str:
        """Reduce text to its absolute simplest form. ELI5 mode."""
        report = self._safety.validate_input(text)
        if not report.is_safe:
            return "(input could not be processed)"
        text = report.sanitized_text or text
        self._sync_persona()
        raw = self._synthesizer.simplify(text)
        return self._sensory.format_output(raw)

    def keywords(self, text: str, top_n: int = 10) -> list[dict[str, Any]]:
        """Extract keywords/highlights from text.

        Returns list of dicts with: text, priority, context, category.
        """
        report = self._safety.validate_input(text)
        if not report.is_safe:
            return []
        text = report.sanitized_text or text
        top_n = max(1, min(top_n, MAX_HIGHLIGHTS))
        highlights = self._synthesizer.extract_keywords(text, top_n=top_n)
        return [
            {
                "text": h.text,
                "priority": h.priority.name.lower(),
                "context": h.context,
                "category": h.category,
            }
            for h in highlights
        ]

    # ------------------------------------------------------------------
    # Mission 3: Make knowledge accessible
    # ------------------------------------------------------------------

    def explore(
        self,
        concept: str,
        pattern: str | None = None,
    ) -> NavigationResult | None:
        """Explore a concept through a cognitive pattern lens.

        Args:
            concept: What to explore (e.g. "cache", "recursion", "database").
            pattern: Preferred pattern (e.g. "flow", "spatial", "rhythm").

        Returns:
            NavigationResult with lens (analogy, ELI5, visual hint),
            or None if concept not in library.
        """
        # Safety: validate concept name
        if not concept or not isinstance(concept, str) or len(concept) > 100:
            return None
        self._sync_persona()
        return self._navigator.explore(concept, preferred_pattern=pattern)

    def try_different(
        self,
        concept: str,
        resonance: ResonanceLevel = ResonanceLevel.SILENT,
    ) -> NavigationResult | None:
        """Previous lens didn't click. Try a different one.

        Args:
            concept: The concept to re-explore.
            resonance: How well the previous lens worked (silent/hum/ring).

        Returns:
            A different NavigationResult, or None if no alternatives.
        """
        return self._navigator.try_different(concept, feedback=resonance)

    def eli5(self, concept: str) -> str:
        """Explain Like I'm 5. Simplest possible explanation of a concept."""
        return self._navigator.simplify(concept)

    @property
    def concepts(self) -> list[str]:
        """List all concepts available in the Pattern Navigator."""
        return self._navigator.available_concepts

    # ------------------------------------------------------------------
    # Mission 1: Understand the user
    # ------------------------------------------------------------------

    def set_user(self, **traits: Any) -> PersonaProfile:
        """Set user traits explicitly. Always overrides auto-detection.

        Accepted traits:
            expertise: "child", "beginner", "familiar", "proficient", "expert"
            cognitive_style: "visual", "narrative", "analytical", "kinesthetic"
            tone: "playful", "warm", "direct", "academic"
            depth: "espresso", "americano", "cold_brew"
            attention_span: "short", "medium", "long"
            age_group: "child", "teen", "adult", "elder"
            challenges: ["dyslexia", "low_vision", "adhd", ...]
            interests: ["tech", "science", "art", ...]
            language: "en", "bn", etc.

        Returns:
            Updated PersonaProfile.
        """
        profile = self._persona_engine.set_explicit(**traits)
        self._sync_persona()
        logger.info("Instrument: user traits updated: %s", list(traits.keys()))
        return profile

    @property
    def user(self) -> PersonaProfile:
        """Current user persona profile."""
        return self._persona_engine.profile

    def observe(self, text: str) -> None:
        """Feed a text observation into the persona engine.

        Use this to help the tool learn about the user from their
        writing style, vocabulary, and phrasing — without synthesizing.
        """
        if not isinstance(text, str) or not text.strip():
            return
        # Cap observation length to prevent memory abuse
        capped = text[:2000]
        self._persona_engine.observe(
            InteractionSignal(signal_type="query", content=capped)
        )
        self._sync_persona()

    # ------------------------------------------------------------------
    # Feedback & Adaptation
    # ------------------------------------------------------------------

    def feedback(
        self,
        too_complex: bool | None = None,
        too_simple: bool | None = None,
        resonance: ResonanceLevel | None = None,
        concept: str | None = None,
        pattern: str | None = None,
    ) -> None:
        """Give feedback. The tool adapts.

        Args:
            too_complex: Content was too hard to follow.
            too_simple: Content was too basic/obvious.
            resonance: How well the last explanation clicked (silent/hum/ring).
            concept: Which concept the feedback is about.
            pattern: Which pattern lens the feedback is about.
        """
        if too_complex is not None or too_simple is not None:
            self._scaffold.feedback(
                too_complex=too_complex, too_simple=too_simple
            )
            # Also feed into persona engine
            if too_complex:
                self._persona_engine.observe(
                    InteractionSignal(
                        signal_type="feedback", content="too complex"
                    )
                )
            elif too_simple:
                self._persona_engine.observe(
                    InteractionSignal(
                        signal_type="feedback", content="too simple"
                    )
                )

        if resonance and concept and pattern:
            self._persona_engine.record_resonance(concept, pattern, resonance)
            self._navigator.feedback(concept, pattern, resonance)

        self._sync_persona()

    # ------------------------------------------------------------------
    # Sensory / Accessibility
    # ------------------------------------------------------------------

    def set_sensory(self, profile: SensoryProfile | str) -> str:
        """Switch sensory profile for output formatting.

        Args:
            profile: Profile name or SensoryProfile enum.

        Returns:
            Description of active adaptations.
        """
        if isinstance(profile, str):
            profile = SensoryProfile(profile)
        self._sensory.apply_profile(profile)
        return self._sensory.explain_current()

    @property
    def sensory_info(self) -> str:
        """Description of current sensory adaptations."""
        return self._sensory.explain_current()

    # ------------------------------------------------------------------
    # Extensibility
    # ------------------------------------------------------------------

    def register_concept(
        self, concept: str, lenses: list[dict[str, str]]
    ) -> None:
        """Add custom concept lenses to the Navigator.

        Args:
            concept: Concept name (e.g. "blockchain").
            lenses: List of dicts with keys: pattern, analogy, eli5,
                    visual_hint, when_useful.
        """
        # Safety: validate concept registration
        name_report = self._safety.validate_concept_name(concept)
        if not name_report.is_safe:
            logger.warning("Instrument.register_concept: rejected: %s", name_report.reasons)
            return

        total_concepts = len(self._navigator.available_concepts)
        if total_concepts >= MAX_REGISTERED_CONCEPTS:
            logger.warning(
                "Instrument.register_concept: concept cap reached (%d)",
                MAX_REGISTERED_CONCEPTS,
            )
            return

        parsed = [
            PatternLens(
                pattern=l["pattern"],
                analogy=l["analogy"],
                eli5=l["eli5"],
                visual_hint=l.get("visual_hint", ""),
                when_useful=l.get("when_useful", ""),
            )
            for l in lenses
        ]
        self._navigator.register_concept(concept, parsed)

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    def explain(self, topic: str = "mycelium") -> str:
        """Plain-language explanation of what Mycelium does.

        Args:
            topic: What to explain. Options: "mycelium", "cache", "pubsub",
                   "rate_limit", "leaderboard", or any registered concept.

        Returns:
            Simple explanation string.
        """
        builtin_explanations = {
            "mycelium": (
                "Mycelium is a tool that takes complex information and makes it "
                "simple. Give it a document, it gives you the gist. Give it a "
                "concept, it explains it with an analogy that fits how you think. "
                "It adapts to you — not the other way around."
            ),
            "synthesize": (
                "You give it text. It finds the important parts, pulls out "
                "keywords, and writes a short version. Like squeezing an "
                "orange — you get the juice, not the pulp."
            ),
            "explore": (
                "Pick a concept. Mycelium shows it to you through a 'lens' — "
                "a metaphor or analogy. Didn't click? Try a different lens. "
                "Like looking at the same mountain from different angles."
            ),
            "feedback": (
                "Tell it 'too complex' or 'too simple.' It adjusts. "
                "Like a conversation — the more you talk, the better it "
                "understands how to explain things to you."
            ),
        }

        if topic in builtin_explanations:
            return self._sensory.format_output(builtin_explanations[topic])

        # Try the navigator
        result = self._navigator.explore(topic)
        if result:
            return self._sensory.format_output(result.lens.eli5)

        return self._sensory.format_output(
            f"I don't have a built-in explanation for '{topic}' yet. "
            f"You can add one with register_concept()."
        )

    def __repr__(self) -> str:
        persona = self._persona_engine.profile
        return (
            f"Instrument("
            f"expertise={persona.expertise.value}, "
            f"style={persona.cognitive_style.value}, "
            f"tone={persona.tone.value}, "
            f"depth={persona.depth.value}, "
            f"sensory={self._sensory.profile.value})"
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @property
    def safety_stats(self) -> dict[str, Any]:
        """Safety check statistics."""
        return self._safety.stats

    def _sync_persona(self) -> None:
        """Propagate persona changes to all components."""
        profile = self._persona_engine.profile
        self._synthesizer.persona = profile
        self._navigator.persona = profile
        self._scaffold.persona = profile
