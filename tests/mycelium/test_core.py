"""Tests for Mycelium core types — grounded in quantifiable physics.

Validates Spore, PersonaProfile, SynthesisResult, Highlight using
measurable physical constants and mathematical relationships.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

import pytest

from mycelium.core import (
    CognitiveStyle,
    Depth,
    EngagementTone,
    ExpertiseLevel,
    Highlight,
    HighlightPriority,
    PersonaProfile,
    ResonanceLevel,
    SignalType,
    Spore,
    SynthesisResult,
)


class TestSpore:
    """Spore is the fundamental data unit — like a photon carrying energy."""

    def test_spore_creation_with_defaults(self) -> None:
        s = Spore(key="wavelength:visible", value=550e-9)
        assert s.key == "wavelength:visible"
        assert s.value == 550e-9  # 550nm green light
        assert s.signal_type == SignalType.NUTRIENT
        assert s.ttl is None
        assert s.priority == 1
        assert s.access_count == 0
        assert isinstance(s.created_at, datetime)

    def test_spore_fingerprint_uniqueness(self) -> None:
        """Different data produces different fingerprints — like different photon energies."""
        s1 = Spore(key="freq:radio", value=100e6)  # 100 MHz
        s2 = Spore(key="freq:microwave", value=2.45e9)  # 2.45 GHz
        assert s1.fingerprint() != s2.fingerprint()

    def test_spore_fingerprint_deterministic(self) -> None:
        """Same data always produces same fingerprint — physical law consistency."""
        s1 = Spore(key="c", value=299_792_458)
        s2 = Spore(key="c", value=299_792_458)
        assert s1.fingerprint() == s2.fingerprint()

    def test_spore_ttl_expiration(self) -> None:
        """Spore expires after TTL — like radioactive half-life."""
        s = Spore(key="isotope:C14", value="5730_years", ttl=0)
        time.sleep(0.01)
        assert s.is_expired() is True

    def test_spore_no_ttl_never_expires(self) -> None:
        """No TTL means permanent — like a conservation law."""
        s = Spore(key="E=mc2", value="mass_energy_equivalence")
        assert s.is_expired() is False

    def test_spore_touch_increments_access(self) -> None:
        """Tracking access — like measuring photon detection events."""
        s = Spore(key="detector:count", value=0)
        assert s.access_count == 0
        s.touch()
        s.touch()
        s.touch()
        assert s.access_count == 3

    def test_spore_signal_types(self) -> None:
        """Three signal types mirror mycelium's chemical categories."""
        assert SignalType.NUTRIENT == "nutrient"
        assert SignalType.DEFENSE == "defense"
        assert SignalType.GROWTH == "growth"

    def test_spore_metadata_carries_context(self) -> None:
        """Metadata enriches the spore — like a photon's polarization state."""
        s = Spore(
            key="photon",
            value=3e8,
            metadata={"polarization": "horizontal", "wavelength_nm": 632.8},
        )
        assert s.metadata["polarization"] == "horizontal"
        assert s.metadata["wavelength_nm"] == 632.8


class TestPersonaProfile:
    """PersonaProfile captures who the user is — tested with expertise levels
    mapping to physics knowledge tiers."""

    def test_default_persona_is_beginner(self) -> None:
        p = PersonaProfile()
        assert p.expertise == ExpertiseLevel.BEGINNER
        assert p.cognitive_style == CognitiveStyle.NARRATIVE
        assert p.tone == EngagementTone.WARM
        assert p.depth == Depth.AMERICANO

    def test_effective_depth_child_gets_espresso(self) -> None:
        """Children get simplest depth — like explaining gravity with an apple."""
        p = PersonaProfile(expertise=ExpertiseLevel.CHILD)
        assert p.effective_depth() == Depth.ESPRESSO

    def test_effective_depth_expert_gets_cold_brew(self) -> None:
        """Experts get full depth — like a research paper with equations."""
        p = PersonaProfile(expertise=ExpertiseLevel.EXPERT)
        assert p.effective_depth() == Depth.COLD_BREW

    def test_effective_depth_familiar_gets_americano(self) -> None:
        p = PersonaProfile(expertise=ExpertiseLevel.FAMILIAR)
        assert p.effective_depth() == Depth.AMERICANO

    def test_resonance_tracking(self) -> None:
        """Resonance feedback accumulates — like signal averaging in spectroscopy."""
        p = PersonaProfile()
        p.record_resonance("cache", "flow", ResonanceLevel.RING)
        p.record_resonance("cache", "spatial", ResonanceLevel.SILENT)
        assert len(p.resonance_history) == 2
        assert "flow" in p.preferred_patterns
        assert "spatial" not in p.preferred_patterns

    def test_challenges_field_stores_accessibility_needs(self) -> None:
        p = PersonaProfile(challenges=["dyslexia", "low_vision"])
        assert "dyslexia" in p.challenges
        assert len(p.challenges) == 2

    def test_all_expertise_levels_exist(self) -> None:
        """Five levels spanning full range — like electromagnetic spectrum bands."""
        levels = list(ExpertiseLevel)
        assert len(levels) == 5
        assert ExpertiseLevel.CHILD in levels
        assert ExpertiseLevel.EXPERT in levels

    def test_all_cognitive_styles_exist(self) -> None:
        styles = list(CognitiveStyle)
        assert len(styles) == 4

    def test_all_engagement_tones_exist(self) -> None:
        tones = list(EngagementTone)
        assert len(tones) == 4


class TestHighlight:
    """Highlights are extracted key points — like spectral emission lines."""

    def test_highlight_creation(self) -> None:
        h = Highlight(
            text="wavelength",
            priority=HighlightPriority.CRITICAL,
            context="...wavelength of 550 nanometers...",
            category="concept",
            position=42,
        )
        assert h.text == "wavelength"
        assert h.priority == HighlightPriority.CRITICAL
        assert h.position == 42

    def test_highlight_priority_ordering(self) -> None:
        """Priorities are ordered — like energy levels in an atom."""
        assert HighlightPriority.LOW < HighlightPriority.MEDIUM
        assert HighlightPriority.MEDIUM < HighlightPriority.HIGH
        assert HighlightPriority.HIGH < HighlightPriority.CRITICAL


class TestSynthesisResult:
    """SynthesisResult carries compressed meaning — like Fourier coefficients
    compressing a signal into fundamental frequencies."""

    def test_synthesis_result_defaults(self) -> None:
        r = SynthesisResult(gist="Light is electromagnetic radiation.")
        assert r.gist == "Light is electromagnetic radiation."
        assert r.highlights == []
        assert r.summary == ""
        assert r.compression_ratio == 0.0
        assert r.resonance == ResonanceLevel.HUM

    def test_synthesis_result_compression_ratio_is_bounded(self) -> None:
        """Compression ratio must be 0..1 — like efficiency in thermodynamics."""
        r = SynthesisResult(
            gist="E=hf",
            source_length=1000,
            compression_ratio=0.004,
        )
        assert 0.0 <= r.compression_ratio <= 1.0

    def test_synthesis_result_as_dict_serializes(self) -> None:
        r = SynthesisResult(
            gist="Speed of light is constant.",
            highlights=[Highlight(text="light", priority=HighlightPriority.CRITICAL, category="concept")],
            compression_ratio=0.05,
            depth_used=Depth.ESPRESSO,
            patterns_applied=["flow", "repetition"],
        )
        d = r.as_dict()
        assert d["gist"] == "Speed of light is constant."
        assert len(d["highlights"]) == 1
        assert d["highlights"][0]["text"] == "light"
        assert d["depth"] == "espresso"
        assert "flow" in d["patterns"]


class TestDepthEnum:
    """Three depths — like three states of matter (solid/liquid/gas)."""

    def test_espresso_is_simplest(self) -> None:
        assert Depth.ESPRESSO == "espresso"

    def test_cold_brew_is_deepest(self) -> None:
        assert Depth.COLD_BREW == "cold_brew"

    def test_all_depths_exist(self) -> None:
        assert len(list(Depth)) == 3


class TestResonanceLevel:
    """Three resonance levels — like standing wave harmonics."""

    def test_silent_means_no_resonance(self) -> None:
        assert ResonanceLevel.SILENT == "silent"

    def test_ring_means_full_resonance(self) -> None:
        assert ResonanceLevel.RING == "ring"

    def test_all_levels_exist(self) -> None:
        assert len(list(ResonanceLevel)) == 3
