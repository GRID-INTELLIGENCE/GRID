"""Integration tests for Mycelium Instrument — end-to-end scenarios.

Uses real physics domain texts to validate the full pipeline:
  Instrument → PersonaEngine → Synthesizer → Navigator → Scaffold → Sensory

Each test scenario is grounded in a specific physics domain with
quantifiable assertions against known physical constants and facts.
"""

from __future__ import annotations

import pytest

from mycelium.core import Depth, ExpertiseLevel, ResonanceLevel
from mycelium.instrument import Instrument
from mycelium.sensory import SensoryProfile
from tests.mycelium.conftest import (
    ECOSYSTEM_ENERGY_TEXT,
    ECOSYSTEM_EXPECTED_KEYWORDS,
    ELECTROMAGNETIC_SPECTRUM_TEXT,
    EM_EXPECTED_KEYWORDS,
    LATENT_HEAT_FUSION_J_PER_G,
    PHASE_EXPECTED_KEYWORDS,
    PHASE_TRANSITIONS_TEXT,
    POLAR_EXPECTED_KEYWORDS,
    POLAR_THERMODYNAMICS_TEXT,
    SPEED_OF_LIGHT_MPS,
    VOSTOK_RECORD_TEMP_C,
)


class TestEMSpectrumSynthesis:
    """Electromagnetic spectrum — signal transport domain.

    Facts: c = 299,792,458 m/s, E = hf, wavelength × frequency = c.
    This domain tests synthesis of continuous spectrum relationships.
    """

    def test_synthesize_extracts_em_gist(self, instrument: Instrument) -> None:
        result = instrument.synthesize(ELECTROMAGNETIC_SPECTRUM_TEXT)
        assert len(result.gist) > 0
        # Gist should mention electromagnetic or spectrum or radiation
        lower = result.gist.lower()
        assert any(w in lower for w in ["electromagnetic", "spectrum", "radiation", "frequen"])

    def test_synthesize_finds_em_keywords(self, instrument: Instrument) -> None:
        kws = instrument.keywords(ELECTROMAGNETIC_SPECTRUM_TEXT, top_n=15)
        extracted = {kw["text"].lower() for kw in kws}
        overlap = extracted & EM_EXPECTED_KEYWORDS
        assert len(overlap) >= 4

    def test_speed_of_light_preserved_in_output(self, instrument: Instrument) -> None:
        """Physical constant must survive synthesis — conservation of facts."""
        result = instrument.synthesize(ELECTROMAGNETIC_SPECTRUM_TEXT, depth=Depth.COLD_BREW)
        assert "299" in result.explanation or "299" in result.summary

    def test_child_can_understand_em_spectrum(self, child_instrument: Instrument) -> None:
        """Child persona must still produce output — accessibility guarantee."""
        result = child_instrument.synthesize(ELECTROMAGNETIC_SPECTRUM_TEXT)
        assert len(result.gist) > 0
        assert len(result.scaffolding_applied) > 0

    def test_expert_gets_minimal_scaffolding(self, expert_instrument: Instrument) -> None:
        result = expert_instrument.synthesize(ELECTROMAGNETIC_SPECTRUM_TEXT)
        assert len(result.gist) > 0
        # Expert with COLD_BREW depth gets light or no scaffolding
        assert len(result.scaffolding_applied) <= 4


class TestPhaseTransitionSynthesis:
    """Phase transitions — matter state transformation domain.

    Facts: ice→water at 0°C (334 J/g), water→steam at 100°C (2260 J/g).
    This domain tests synthesis of discrete state changes.
    """

    def test_synthesize_extracts_phase_gist(self, instrument: Instrument) -> None:
        result = instrument.synthesize(PHASE_TRANSITIONS_TEXT)
        lower = result.gist.lower()
        assert any(w in lower for w in ["matter", "phase", "state", "solid", "liquid", "gas", "transition"])

    def test_synthesize_finds_phase_keywords(self, instrument: Instrument) -> None:
        kws = instrument.keywords(PHASE_TRANSITIONS_TEXT, top_n=15)
        extracted = {kw["text"].lower() for kw in kws}
        overlap = extracted & PHASE_EXPECTED_KEYWORDS
        assert len(overlap) >= 3

    def test_latent_heat_values_preserved(self, instrument: Instrument) -> None:
        """Quantitative facts must survive — like energy conservation."""
        result = instrument.synthesize(PHASE_TRANSITIONS_TEXT, depth=Depth.COLD_BREW)
        combined = result.summary + " " + result.explanation
        # At least one of the key numbers should appear
        assert "334" in combined or "2,260" in combined or "2260" in combined

    def test_summarize_preserves_key_sentences(self, instrument: Instrument) -> None:
        summary = instrument.summarize(PHASE_TRANSITIONS_TEXT, sentences=3)
        assert len(summary) > 50
        assert len(summary) < len(PHASE_TRANSITIONS_TEXT)

    def test_simplify_is_shorter_than_original(self, instrument: Instrument) -> None:
        simple = instrument.simplify(PHASE_TRANSITIONS_TEXT)
        assert len(simple) < len(PHASE_TRANSITIONS_TEXT)
        assert len(simple) > 10


class TestPolarThermodynamicsSynthesis:
    """Polar thermodynamics — environmental thermostate domain.

    Facts: Vostok -89.2°C, Antarctic ice 26.5M km³, albedo 0.90.
    This domain tests synthesis of complex environmental patterns.
    """

    def test_synthesize_extracts_polar_gist(self, instrument: Instrument) -> None:
        result = instrument.synthesize(POLAR_THERMODYNAMICS_TEXT)
        lower = result.gist.lower()
        assert any(w in lower for w in ["arctic", "antarctic", "polar", "temperature", "ice"])

    def test_synthesize_finds_polar_keywords(self, instrument: Instrument) -> None:
        kws = instrument.keywords(POLAR_THERMODYNAMICS_TEXT, top_n=15)
        extracted = {kw["text"].lower() for kw in kws}
        overlap = extracted & POLAR_EXPECTED_KEYWORDS
        assert len(overlap) >= 3

    def test_vostok_temperature_preserved(self, instrument: Instrument) -> None:
        """Record temperature must survive — it's a measured physical fact."""
        result = instrument.synthesize(POLAR_THERMODYNAMICS_TEXT, depth=Depth.COLD_BREW)
        combined = result.summary + " " + result.explanation
        assert "89" in combined  # -89.2°C

    def test_compression_ratio_within_bounds(self, instrument: Instrument) -> None:
        """Compression must be meaningful — not trivial, not lossy."""
        result = instrument.synthesize(POLAR_THERMODYNAMICS_TEXT)
        assert 0.01 < result.compression_ratio < 0.5

    def test_patterns_detected_in_polar_text(self, instrument: Instrument) -> None:
        result = instrument.synthesize(POLAR_THERMODYNAMICS_TEXT)
        assert len(result.patterns_applied) >= 1


class TestEcosystemEnergySynthesis:
    """Ecosystem energy flow — biological thermodynamics domain.

    Facts: 10% trophic transfer, ~2% photosynthesis efficiency,
    6CO2 + 6H2O → C6H12O6 + 6O2.
    """

    def test_synthesize_extracts_ecosystem_gist(self, instrument: Instrument) -> None:
        result = instrument.synthesize(ECOSYSTEM_ENERGY_TEXT)
        lower = result.gist.lower()
        assert any(w in lower for w in ["energy", "ecosystem", "thermodynamic", "trophic"])

    def test_synthesize_finds_ecosystem_keywords(self, instrument: Instrument) -> None:
        kws = instrument.keywords(ECOSYSTEM_ENERGY_TEXT, top_n=15)
        extracted = {kw["text"].lower() for kw in kws}
        overlap = extracted & ECOSYSTEM_EXPECTED_KEYWORDS
        assert len(overlap) >= 3


class TestCrossDomainPersonaAdaptation:
    """Persona adaptation across domains — like the same instrument
    measuring different phenomena."""

    def test_child_gets_more_scaffolding_than_expert(self) -> None:
        child = Instrument()
        child.set_user(expertise="child")
        expert = Instrument()
        expert.set_user(expertise="expert")

        cr = child.synthesize(ELECTROMAGNETIC_SPECTRUM_TEXT)
        er = expert.synthesize(ELECTROMAGNETIC_SPECTRUM_TEXT)

        assert len(cr.scaffolding_applied) >= len(er.scaffolding_applied)

    def test_feedback_loop_changes_output(self, instrument: Instrument) -> None:
        """Feedback must materially change output — like adjusting telescope focus."""
        r1 = instrument.synthesize(PHASE_TRANSITIONS_TEXT)
        instrument.feedback(too_complex=True)
        r2 = instrument.synthesize(PHASE_TRANSITIONS_TEXT)
        # After "too complex" feedback, scaffolding should increase
        assert len(r2.scaffolding_applied) >= len(r1.scaffolding_applied)

    def test_sensory_profile_changes_formatting(self, instrument: Instrument) -> None:
        """Switching sensory profile must change output format."""
        r_default = instrument.synthesize(POLAR_THERMODYNAMICS_TEXT)
        instrument.set_sensory("cognitive")
        r_cognitive = instrument.synthesize(POLAR_THERMODYNAMICS_TEXT)
        # Cognitive profile simplifies punctuation, so output differs
        assert r_default.explanation != r_cognitive.explanation or r_default.gist != r_cognitive.gist


class TestNavigatorIntegration:
    """Navigator integration through Instrument interface."""

    def test_explore_concept_from_instrument(self, instrument: Instrument) -> None:
        nav = instrument.explore("cache")
        assert nav is not None
        assert len(nav.lens.eli5) > 0

    def test_try_different_from_instrument(self, instrument: Instrument) -> None:
        instrument.explore("cache")
        alt = instrument.try_different("cache", resonance=ResonanceLevel.SILENT)
        assert alt is not None

    def test_eli5_from_instrument(self, instrument: Instrument) -> None:
        result = instrument.eli5("recursion")
        assert len(result) > 10
        assert "box" in result.lower() or "smaller" in result.lower()

    def test_concepts_list_nonempty(self, instrument: Instrument) -> None:
        assert len(instrument.concepts) >= 10

    def test_explain_mycelium(self, instrument: Instrument) -> None:
        explanation = instrument.explain("mycelium")
        assert "complex" in explanation.lower() or "simple" in explanation.lower()

    def test_register_custom_concept(self, instrument: Instrument) -> None:
        instrument.register_concept(
            "thermodynamics",
            [
                {
                    "pattern": "flow",
                    "analogy": "Heat flows from hot to cold, like water downhill.",
                    "eli5": "Hot things cool down. Cold things warm up.",
                    "visual_hint": "Picture two cups of water mixing temperatures.",
                    "when_useful": "When understanding energy transfer.",
                }
            ],
        )
        nav = instrument.explore("thermodynamics")
        assert nav is not None
        assert "hot" in nav.lens.eli5.lower()


class TestInstrumentRepr:
    """Instrument self-description — transparency."""

    def test_repr_contains_persona_info(self, instrument: Instrument) -> None:
        r = repr(instrument)
        assert "expertise=" in r
        assert "style=" in r
        assert "sensory=" in r

    def test_repr_updates_after_set_user(self, instrument: Instrument) -> None:
        instrument.set_user(expertise="expert", tone="direct")
        r = repr(instrument)
        assert "expert" in r
        assert "direct" in r
