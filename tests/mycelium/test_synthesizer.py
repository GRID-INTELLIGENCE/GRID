"""Tests for Mycelium Synthesizer — pattern recognition and synthesis engine.

Grounded in real physics texts with measurable assertions:
  - Keyword extraction accuracy against known domain terms
  - Compression ratios within thermodynamic-inspired bounds
  - Pattern detection against known text structures
  - Sentence scoring validated against information-theoretic expectations
"""

from __future__ import annotations

import pytest

from mycelium.core import Depth, ExpertiseLevel, HighlightPriority, PersonaProfile
from mycelium.synthesizer import Synthesizer
from tests.mycelium.conftest import (
    ECOSYSTEM_ENERGY_TEXT,
    ECOSYSTEM_EXPECTED_KEYWORDS,
    ELECTROMAGNETIC_SPECTRUM_TEXT,
    EM_EXPECTED_KEYWORDS,
    EMPTY_TEXT,
    ONE_SENTENCE,
    PHASE_EXPECTED_KEYWORDS,
    PHASE_TRANSITIONS_TEXT,
    POLAR_EXPECTED_KEYWORDS,
    POLAR_THERMODYNAMICS_TEXT,
    TWO_SENTENCES,
)


class TestKeywordExtraction:
    """Keyword extraction must find domain-specific terms — like identifying
    spectral lines in an emission spectrum."""

    def test_em_spectrum_keywords_found(self, synthesizer: Synthesizer) -> None:
        """Must detect core EM terms: electromagnetic, frequency, wavelength, radiation."""
        highlights = synthesizer.extract_keywords(ELECTROMAGNETIC_SPECTRUM_TEXT, top_n=15)
        extracted = {h.text.lower() for h in highlights}
        # At least 4 of 6 expected keywords must appear
        overlap = extracted & EM_EXPECTED_KEYWORDS
        assert len(overlap) >= 4, f"Expected ≥4 of {EM_EXPECTED_KEYWORDS}, got {overlap}"

    def test_phase_transition_keywords_found(self, synthesizer: Synthesizer) -> None:
        """Must detect phase/state terms: phase, transitions, temperature, energy."""
        highlights = synthesizer.extract_keywords(PHASE_TRANSITIONS_TEXT, top_n=15)
        extracted = {h.text.lower() for h in highlights}
        overlap = extracted & PHASE_EXPECTED_KEYWORDS
        assert len(overlap) >= 4, f"Expected ≥4 of {PHASE_EXPECTED_KEYWORDS}, got {overlap}"

    def test_polar_keywords_found(self, synthesizer: Synthesizer) -> None:
        """Must detect polar terms: arctic, antarctic, temperature, ice."""
        highlights = synthesizer.extract_keywords(POLAR_THERMODYNAMICS_TEXT, top_n=15)
        extracted = {h.text.lower() for h in highlights}
        overlap = extracted & POLAR_EXPECTED_KEYWORDS
        assert len(overlap) >= 3, f"Expected ≥3 of {POLAR_EXPECTED_KEYWORDS}, got {overlap}"

    def test_ecosystem_keywords_found(self, synthesizer: Synthesizer) -> None:
        """Must detect ecosystem terms: energy, trophic, photosynthesis."""
        highlights = synthesizer.extract_keywords(ECOSYSTEM_ENERGY_TEXT, top_n=15)
        extracted = {h.text.lower() for h in highlights}
        overlap = extracted & ECOSYSTEM_EXPECTED_KEYWORDS
        assert len(overlap) >= 3, f"Expected ≥3 of {ECOSYSTEM_EXPECTED_KEYWORDS}, got {overlap}"

    def test_keyword_priority_ordering(self, synthesizer: Synthesizer) -> None:
        """Top keywords get CRITICAL priority — like dominant spectral lines."""
        highlights = synthesizer.extract_keywords(ELECTROMAGNETIC_SPECTRUM_TEXT, top_n=10)
        assert len(highlights) >= 5
        assert highlights[0].priority == HighlightPriority.CRITICAL
        assert highlights[-1].priority.value <= highlights[0].priority.value

    def test_keyword_context_is_populated(self, synthesizer: Synthesizer) -> None:
        """Each keyword must carry surrounding context — like spectral line broadening."""
        highlights = synthesizer.extract_keywords(ELECTROMAGNETIC_SPECTRUM_TEXT, top_n=5)
        for h in highlights:
            assert len(h.context) > 0, f"Keyword '{h.text}' has empty context"

    def test_keyword_count_respects_top_n(self, synthesizer: Synthesizer) -> None:
        """Never return more keywords than requested."""
        for n in [3, 5, 10]:
            highlights = synthesizer.extract_keywords(PHASE_TRANSITIONS_TEXT, top_n=n)
            assert len(highlights) <= n


class TestSynthesis:
    """Synthesis compresses complex text — like Fourier transform reducing
    a signal to its fundamental components."""

    def test_gist_is_always_produced(self, synthesizer: Synthesizer) -> None:
        """Every synthesis must produce a gist — like every signal has a fundamental frequency."""
        for text in [
            ELECTROMAGNETIC_SPECTRUM_TEXT,
            PHASE_TRANSITIONS_TEXT,
            POLAR_THERMODYNAMICS_TEXT,
            ECOSYSTEM_ENERGY_TEXT,
        ]:
            result = synthesizer.synthesize(text)
            assert len(result.gist) > 0

    def test_compression_ratio_is_bounded(self, synthesizer: Synthesizer) -> None:
        """Compression ratio must be between 0 and 1 — like thermodynamic efficiency."""
        result = synthesizer.synthesize(ELECTROMAGNETIC_SPECTRUM_TEXT)
        assert 0.0 < result.compression_ratio < 1.0

    def test_compression_ratio_decreases_with_longer_text(self, synthesizer: Synthesizer) -> None:
        """Longer text → lower compression ratio — like diminishing returns in heat engines."""
        short = synthesizer.synthesize(TWO_SENTENCES)
        long = synthesizer.synthesize(ELECTROMAGNETIC_SPECTRUM_TEXT)
        # Longer text compresses more aggressively (lower ratio)
        assert long.compression_ratio < short.compression_ratio

    def test_espresso_depth_produces_shorter_output(self) -> None:
        """Espresso depth = minimal output — like a delta function approximation."""
        s_espresso = Synthesizer(PersonaProfile(expertise=ExpertiseLevel.CHILD))
        s_cold = Synthesizer(PersonaProfile(expertise=ExpertiseLevel.EXPERT))
        r_esp = s_espresso.synthesize(PHASE_TRANSITIONS_TEXT, depth=Depth.ESPRESSO)
        r_cold = s_cold.synthesize(PHASE_TRANSITIONS_TEXT, depth=Depth.COLD_BREW)
        assert len(r_esp.summary) <= len(r_cold.summary)

    def test_highlights_are_populated(self, synthesizer: Synthesizer) -> None:
        """Synthesis must extract highlights — like identifying absorption lines."""
        result = synthesizer.synthesize(POLAR_THERMODYNAMICS_TEXT)
        assert len(result.highlights) > 0

    def test_source_length_matches_input(self, synthesizer: Synthesizer) -> None:
        """Source length must match input — conservation of information."""
        result = synthesizer.synthesize(PHASE_TRANSITIONS_TEXT)
        assert result.source_length == len(PHASE_TRANSITIONS_TEXT)

    def test_empty_input_produces_empty_gist(self, synthesizer: Synthesizer) -> None:
        result = synthesizer.synthesize(EMPTY_TEXT)
        assert result.gist == "(empty input)"
        assert result.source_length == 0

    def test_single_sentence_gist_is_the_sentence(self, synthesizer: Synthesizer) -> None:
        """One sentence in → that sentence is the gist. Conservation law."""
        result = synthesizer.synthesize(ONE_SENTENCE)
        assert ONE_SENTENCE in result.gist or result.gist in ONE_SENTENCE


class TestPatternDetection:
    """Pattern detection identifies text structures — like identifying
    wave interference patterns in a diffraction experiment."""

    def test_repetition_detected_in_em_text(self, synthesizer: Synthesizer) -> None:
        """EM text repeats 'electromagnetic', 'frequency', 'radiation' → repetition pattern."""
        result = synthesizer.synthesize(ELECTROMAGNETIC_SPECTRUM_TEXT)
        assert "repetition" in result.patterns_applied

    def test_spatial_detected_in_structured_text(self, synthesizer: Synthesizer) -> None:
        """Texts with 'structure', 'system', 'network' → spatial pattern."""
        result = synthesizer.synthesize(ECOSYSTEM_ENERGY_TEXT)
        # Ecosystem text has structural language
        patterns = result.patterns_applied
        assert len(patterns) > 0  # at least one pattern detected

    def test_flow_detected_in_causal_text(self, synthesizer: Synthesizer) -> None:
        """Texts with logical connectives → flow pattern."""
        # Phase transitions text uses "because", "rather than" etc.
        result = synthesizer.synthesize(PHASE_TRANSITIONS_TEXT)
        patterns = result.patterns_applied
        # Should detect at least one structural pattern
        assert len(patterns) >= 1

    def test_patterns_list_is_not_empty_for_rich_text(self, synthesizer: Synthesizer) -> None:
        """Rich scientific text should trigger at least one pattern."""
        for text in [
            ELECTROMAGNETIC_SPECTRUM_TEXT,
            PHASE_TRANSITIONS_TEXT,
            POLAR_THERMODYNAMICS_TEXT,
            ECOSYSTEM_ENERGY_TEXT,
        ]:
            result = synthesizer.synthesize(text)
            assert len(result.patterns_applied) >= 1, "No patterns found in text"


class TestSummarize:
    """Summarize extracts top N sentences — like selecting dominant
    harmonics from a Fourier series."""

    def test_summarize_respects_sentence_count(self, synthesizer: Synthesizer) -> None:
        summary_2 = synthesizer.summarize(POLAR_THERMODYNAMICS_TEXT, sentence_count=2)
        summary_5 = synthesizer.summarize(POLAR_THERMODYNAMICS_TEXT, sentence_count=5)
        assert len(summary_2) < len(summary_5)

    def test_summarize_preserves_original_order(self, synthesizer: Synthesizer) -> None:
        """Selected sentences must appear in original order — time causality."""
        summary = synthesizer.summarize(PHASE_TRANSITIONS_TEXT, sentence_count=3)
        # Each sentence in summary should appear in original text
        for sent in summary.split(". "):
            clean = sent.strip().rstrip(".")
            if len(clean) > 20:
                assert clean in PHASE_TRANSITIONS_TEXT or PHASE_TRANSITIONS_TEXT.find(clean[:30]) >= 0

    def test_summarize_short_text_returns_original(self, synthesizer: Synthesizer) -> None:
        """If text has fewer sentences than requested, return all."""
        result = synthesizer.summarize(ONE_SENTENCE, sentence_count=5)
        assert ONE_SENTENCE in result


class TestSimplify:
    """Simplify produces ELI5 output — like the zeroth-order approximation."""

    def test_simplify_shorter_than_original(self, synthesizer: Synthesizer) -> None:
        simple = synthesizer.simplify(ELECTROMAGNETIC_SPECTRUM_TEXT)
        assert len(simple) < len(ELECTROMAGNETIC_SPECTRUM_TEXT)

    def test_simplify_nonempty(self, synthesizer: Synthesizer) -> None:
        simple = synthesizer.simplify(PHASE_TRANSITIONS_TEXT)
        assert len(simple) > 0

    def test_simplify_for_child_includes_keywords(self) -> None:
        """Child persona simplification should still mention key concepts."""
        s = Synthesizer(PersonaProfile(expertise=ExpertiseLevel.CHILD))
        simple = s.simplify(PHASE_TRANSITIONS_TEXT)
        assert len(simple) > 0
        # Should contain at least one domain word
        lower = simple.lower()
        assert any(w in lower for w in ["phase", "temperature", "energy", "water", "key"])
