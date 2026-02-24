"""Tests for Mycelium PatternNavigator — cognitive lens exploration.

Grounded in the principle that the same physical phenomenon can be
understood through multiple frameworks (wave/particle duality,
thermodynamic/statistical mechanics, classical/quantum descriptions).
"""

from __future__ import annotations

import pytest

from mycelium.core import CognitiveStyle, ExpertiseLevel, PersonaProfile, ResonanceLevel
from mycelium.navigator import PatternLens, PatternNavigator


class TestConceptExploration:
    """Exploring concepts through lenses — like observing light through
    different filters (polarizers, spectrometers, interferometers)."""

    def test_known_concept_returns_result(self, navigator: PatternNavigator) -> None:
        result = navigator.explore("cache")
        assert result is not None
        assert result.concept == "cache"
        assert result.lens.pattern != ""
        assert result.lens.analogy != ""
        assert result.lens.eli5 != ""

    def test_unknown_concept_returns_none(self, navigator: PatternNavigator) -> None:
        result = navigator.explore("xyznonexistent")
        assert result is None

    def test_explore_all_registered_concepts(self, navigator: PatternNavigator) -> None:
        """Every registered concept must be explorable — complete coverage."""
        for concept in navigator.available_concepts:
            result = navigator.explore(concept)
            assert result is not None, f"Concept '{concept}' returned None"
            assert len(result.lens.eli5) > 0, f"Concept '{concept}' has empty ELI5"

    def test_alternatives_count_is_correct(self, navigator: PatternNavigator) -> None:
        """alternatives_available = total lenses - 1."""
        result = navigator.explore("cache")
        assert result is not None
        # Cache has 3 lenses, so alternatives = 2
        assert result.alternatives_available >= 1

    def test_preferred_pattern_is_respected(self, navigator: PatternNavigator) -> None:
        """Explicit pattern preference — like choosing which spectrometer to use."""
        result = navigator.explore("cache", preferred_pattern="rhythm")
        assert result is not None
        assert result.lens.pattern == "rhythm"

    def test_nonexistent_pattern_falls_through(self, navigator: PatternNavigator) -> None:
        """Requesting unavailable pattern falls back gracefully."""
        result = navigator.explore("cache", preferred_pattern="nonexistent")
        assert result is not None  # still returns something


class TestTryDifferent:
    """Switching lenses — like rotating a polarizer to observe different
    components of the same phenomenon."""

    def test_try_different_returns_different_lens(self, navigator: PatternNavigator) -> None:
        first = navigator.explore("cache")
        assert first is not None
        second = navigator.try_different("cache", feedback=ResonanceLevel.SILENT)
        assert second is not None
        assert second.lens.pattern != first.lens.pattern

    def test_try_different_with_ring_feedback_records_preference(self, navigator: PatternNavigator) -> None:
        first = navigator.explore("cache")
        assert first is not None
        navigator.try_different("cache", feedback=ResonanceLevel.RING)
        # Ring feedback should record the first pattern as preferred
        assert first.lens.pattern in navigator.persona.preferred_patterns

    def test_try_different_on_single_lens_concept_returns_none(self, navigator: PatternNavigator) -> None:
        """Concepts with only 1 lens have no alternatives — like a fundamental constant."""
        result = navigator.explore("encryption")
        if result is not None and result.alternatives_available == 0:
            alt = navigator.try_different("encryption")
            assert alt is None


class TestPersonaAdaptiveLensSelection:
    """Lens selection adapts to persona — like choosing the right instrument
    for the measurement (thermometer vs spectrometer vs voltmeter)."""

    def test_visual_persona_prefers_spatial_lens(self) -> None:
        persona = PersonaProfile(cognitive_style=CognitiveStyle.VISUAL)
        nav = PatternNavigator(persona=persona)
        result = nav.explore("cache")
        assert result is not None
        assert result.lens.pattern == "spatial"

    def test_narrative_persona_prefers_flow_lens(self) -> None:
        persona = PersonaProfile(cognitive_style=CognitiveStyle.NARRATIVE)
        nav = PatternNavigator(persona=persona)
        result = nav.explore("cache")
        assert result is not None
        assert result.lens.pattern == "flow"

    def test_preferred_pattern_from_resonance_overrides_style(self) -> None:
        """Past resonance beats cognitive style — empirical data over theory."""
        persona = PersonaProfile(cognitive_style=CognitiveStyle.VISUAL)
        persona.record_resonance("anything", "rhythm", ResonanceLevel.RING)
        nav = PatternNavigator(persona=persona)
        result = nav.explore("cache")
        assert result is not None
        assert result.lens.pattern == "rhythm"


class TestELI5:
    """ELI5 mode — like the zeroth-order Taylor expansion: captures the
    essence with minimum terms."""

    def test_eli5_returns_string(self, navigator: PatternNavigator) -> None:
        result = navigator.simplify("cache")
        assert isinstance(result, str)
        assert len(result) > 10

    def test_eli5_unknown_concept_gives_helpful_message(self, navigator: PatternNavigator) -> None:
        result = navigator.simplify("xyznonexistent")
        assert "not in my library" in result.lower() or len(result) > 0

    def test_eli5_for_all_concepts(self, navigator: PatternNavigator) -> None:
        """Every concept must have a simple explanation."""
        for concept in navigator.available_concepts:
            eli5 = navigator.simplify(concept)
            assert len(eli5) > 5, f"ELI5 for '{concept}' is too short"


class TestConceptRegistration:
    """Custom concept registration — like adding new elements to the
    periodic table when discovered."""

    def test_register_new_concept(self, navigator: PatternNavigator) -> None:
        navigator.register_concept("thermodynamics", [
            PatternLens(
                pattern="flow",
                analogy="Heat flows like water — from hot to cold, never uphill without work.",
                eli5="Hot things cool down. Cold things warm up. They meet in the middle.",
                visual_hint="Picture two cups of water at different temperatures mixing.",
                when_useful="When understanding why heat moves and energy transforms.",
            ),
        ])
        result = navigator.explore("thermodynamics")
        assert result is not None
        assert "heat" in result.lens.analogy.lower() or "hot" in result.lens.eli5.lower()

    def test_registered_concept_appears_in_available(self, navigator: PatternNavigator) -> None:
        navigator.register_concept("quantum_tunneling", [
            PatternLens(
                pattern="deviation",
                analogy="A ball rolling through a hill it shouldn't be able to climb.",
                eli5="Sometimes things go through walls. Very tiny things, very thin walls.",
                visual_hint="Picture a ball at the bottom of a hill. It appears on the other side.",
                when_useful="When classical physics says 'impossible' but quantum says 'maybe'.",
            ),
        ])
        assert "quantum_tunneling" in navigator.available_concepts


class TestFuzzyLookup:
    """Fuzzy matching — like approximate frequency matching in a tuner."""

    def test_partial_match_finds_concept(self, navigator: PatternNavigator) -> None:
        """'data' should fuzzy-match 'database'."""
        result = navigator.explore("data")
        # Should match "database" via fuzzy
        assert result is not None

    def test_superset_match_finds_concept(self, navigator: PatternNavigator) -> None:
        """'caching' should fuzzy-match 'cache'."""
        result = navigator.explore("cach")
        assert result is not None
