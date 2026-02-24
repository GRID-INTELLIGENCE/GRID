"""Tests for Mycelium PersonaEngine — user personality detection and adaptation.

Grounded in signal detection theory: the engine observes interaction signals
and infers traits, like a spectrometer identifying elements from emission lines.
"""

from __future__ import annotations

import pytest

from mycelium.core import (
    CognitiveStyle,
    Depth,
    EngagementTone,
    ExpertiseLevel,
    ResonanceLevel,
)
from mycelium.persona import InteractionSignal, PersonaEngine


class TestExpertiseDetection:
    """Expertise detection from vocabulary — like identifying elements
    from their characteristic spectral lines."""

    def test_tech_jargon_elevates_expertise(self, persona_engine: PersonaEngine) -> None:
        """Dense technical vocabulary → higher expertise detected."""
        tech_query = (
            "How does the Redis cache invalidation work with the API endpoint? "
            "I need to configure the middleware for async throughput optimization "
            "with the microservice container orchestration on Kubernetes."
        )
        # Feed enough signals to trigger detection
        for _ in range(3):
            persona_engine.observe(InteractionSignal(signal_type="query", content=tech_query))

        profile = persona_engine.profile
        assert profile.expertise in (ExpertiseLevel.PROFICIENT, ExpertiseLevel.EXPERT)

    def test_simple_vocabulary_stays_beginner(self, persona_engine: PersonaEngine) -> None:
        """Simple, everyday words → expertise stays low."""
        simple_query = "What does this thing do? How do I use it?"
        for _ in range(3):
            persona_engine.observe(InteractionSignal(signal_type="query", content=simple_query))

        profile = persona_engine.profile
        assert profile.expertise in (ExpertiseLevel.BEGINNER, ExpertiseLevel.FAMILIAR)

    def test_medical_jargon_detected(self, persona_engine: PersonaEngine) -> None:
        """Medical vocabulary triggers domain detection."""
        medical_query = (
            "The diagnosis indicates chronic pathology with contraindication "
            "for the pharmacological treatment given the acute symptomatic presentation."
        )
        for _ in range(3):
            persona_engine.observe(InteractionSignal(signal_type="query", content=medical_query))

        assert "medical" in persona_engine.profile.interests

    def test_science_jargon_detected(self, persona_engine: PersonaEngine) -> None:
        """Scientific vocabulary detected as interest domain."""
        science_query = (
            "The hypothesis requires quantitative empirical validation "
            "with a peer-reviewed statistical methodology and correlation analysis."
        )
        for _ in range(3):
            persona_engine.observe(InteractionSignal(signal_type="query", content=science_query))

        assert "science" in persona_engine.profile.interests


class TestCognitiveStyleDetection:
    """Cognitive style from phrasing — like determining wave polarization
    from measurement orientation."""

    def test_visual_phrases_set_visual_style(self, persona_engine: PersonaEngine) -> None:
        persona_engine.observe(
            InteractionSignal(signal_type="query", content="Show me a diagram of how this looks like")
        )
        assert persona_engine.profile.cognitive_style == CognitiveStyle.VISUAL

    def test_narrative_phrases_set_narrative_style(self, persona_engine: PersonaEngine) -> None:
        persona_engine.observe(
            InteractionSignal(signal_type="query", content="Tell me a story or analogy to explain this")
        )
        assert persona_engine.profile.cognitive_style == CognitiveStyle.NARRATIVE

    def test_analytical_phrases_set_analytical_style(self, persona_engine: PersonaEngine) -> None:
        persona_engine.observe(
            InteractionSignal(signal_type="query", content="Compare the data and statistics, pros and cons")
        )
        assert persona_engine.profile.cognitive_style == CognitiveStyle.ANALYTICAL

    def test_kinesthetic_phrases_set_kinesthetic_style(self, persona_engine: PersonaEngine) -> None:
        persona_engine.observe(
            InteractionSignal(signal_type="query", content="Let me try it hands-on and build something interactive step by step")
        )
        assert persona_engine.profile.cognitive_style == CognitiveStyle.KINESTHETIC


class TestFeedbackAdaptation:
    """Feedback adjusts persona — like a PID controller adjusting to error signal."""

    def test_too_complex_feedback_reduces_depth(self, persona_engine: PersonaEngine) -> None:
        """'Too complex' signal → depth shifts down."""
        persona_engine.set_explicit(depth="cold_brew")
        persona_engine.observe(
            InteractionSignal(signal_type="feedback", content="This is too complex and confusing")
        )
        assert persona_engine.profile.depth == Depth.AMERICANO

    def test_too_simple_feedback_increases_depth(self, persona_engine: PersonaEngine) -> None:
        """'Too simple' signal → depth shifts up."""
        persona_engine.set_explicit(depth="espresso")
        persona_engine.observe(
            InteractionSignal(signal_type="feedback", content="This is too simple, I know this already")
        )
        assert persona_engine.profile.depth == Depth.AMERICANO

    def test_boring_feedback_switches_to_playful(self, persona_engine: PersonaEngine) -> None:
        persona_engine.observe(
            InteractionSignal(signal_type="feedback", content="This is boring and dry")
        )
        assert persona_engine.profile.tone == EngagementTone.PLAYFUL

    def test_depth_floor_at_espresso(self, persona_engine: PersonaEngine) -> None:
        """Cannot go below espresso — like absolute zero in temperature."""
        persona_engine.set_explicit(depth="espresso")
        persona_engine.observe(
            InteractionSignal(signal_type="feedback", content="Too complex")
        )
        assert persona_engine.profile.depth == Depth.ESPRESSO

    def test_depth_ceiling_at_cold_brew(self, persona_engine: PersonaEngine) -> None:
        """Cannot go above cold_brew — like speed of light limit."""
        persona_engine.set_explicit(depth="cold_brew")
        persona_engine.observe(
            InteractionSignal(signal_type="feedback", content="Too simple, I know this")
        )
        assert persona_engine.profile.depth == Depth.COLD_BREW


class TestExplicitOverrides:
    """Explicit traits always override detection — like calibration overriding
    automated measurement."""

    def test_set_explicit_expertise(self, persona_engine: PersonaEngine) -> None:
        persona_engine.set_explicit(expertise="expert")
        assert persona_engine.profile.expertise == ExpertiseLevel.EXPERT

    def test_set_explicit_tone(self, persona_engine: PersonaEngine) -> None:
        persona_engine.set_explicit(tone="academic")
        assert persona_engine.profile.tone == EngagementTone.ACADEMIC

    def test_set_explicit_challenges(self, persona_engine: PersonaEngine) -> None:
        persona_engine.set_explicit(challenges=["dyslexia", "adhd"])
        assert persona_engine.profile.challenges == ["dyslexia", "adhd"]

    def test_set_explicit_age_group(self, persona_engine: PersonaEngine) -> None:
        persona_engine.set_explicit(age_group="child")
        assert persona_engine.profile.age_group == "child"


class TestResonanceTracking:
    """Resonance history — like building up a spectral database
    from repeated measurements."""

    def test_ring_resonance_adds_preferred_pattern(self, persona_engine: PersonaEngine) -> None:
        persona_engine.record_resonance("cache", "flow", ResonanceLevel.RING)
        assert "flow" in persona_engine.profile.preferred_patterns

    def test_silent_resonance_does_not_add_preferred(self, persona_engine: PersonaEngine) -> None:
        persona_engine.record_resonance("cache", "spatial", ResonanceLevel.SILENT)
        assert "spatial" not in persona_engine.profile.preferred_patterns

    def test_resonance_history_accumulates(self, persona_engine: PersonaEngine) -> None:
        persona_engine.record_resonance("cache", "flow", ResonanceLevel.RING)
        persona_engine.record_resonance("api", "cause", ResonanceLevel.HUM)
        persona_engine.record_resonance("recursion", "repetition", ResonanceLevel.RING)
        assert len(persona_engine.profile.resonance_history) == 3


class TestSnapshotConfidence:
    """Confidence grows with signal count — like statistical significance
    growing with sample size."""

    def test_zero_signals_zero_confidence(self, persona_engine: PersonaEngine) -> None:
        snapshot = persona_engine._build_snapshot()
        assert snapshot.confidence == 0.0
        assert snapshot.signals_analyzed == 0

    def test_confidence_grows_with_signals(self, persona_engine: PersonaEngine) -> None:
        for i in range(10):
            persona_engine.observe(
                InteractionSignal(signal_type="query", content=f"query number {i}")
            )
        snapshot = persona_engine._build_snapshot()
        assert snapshot.confidence > 0.0
        assert snapshot.signals_analyzed == 10

    def test_confidence_caps_below_one(self, persona_engine: PersonaEngine) -> None:
        """Confidence never reaches 1.0 — like Heisenberg uncertainty."""
        for i in range(100):
            persona_engine.observe(
                InteractionSignal(signal_type="query", content=f"query {i}")
            )
        snapshot = persona_engine._build_snapshot()
        assert snapshot.confidence <= 0.95


class TestReset:
    """Reset clears all state — like returning to ground state."""

    def test_reset_clears_profile(self, persona_engine: PersonaEngine) -> None:
        persona_engine.set_explicit(expertise="expert", tone="academic")
        persona_engine.reset()
        assert persona_engine.profile.expertise == ExpertiseLevel.BEGINNER
        assert persona_engine.profile.tone == EngagementTone.WARM
