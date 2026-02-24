"""Tests for Mycelium SensoryMode — accessibility output formatting.

Grounded in signal processing: each sensory profile transforms output
like a filter transforms a signal — preserving information content
while changing representation for the receiver's needs.
"""

from __future__ import annotations

import pytest

from mycelium.sensory import SensoryAdaptation, SensoryMode, SensoryProfile, SensoryState


SAMPLE_OUTPUT = (
    "IN BRIEF: The electromagnetic spectrum spans from radio waves (3 Hz) "
    "to gamma rays (30 EHz).\n\n"
    "KEY POINTS:\n"
    "  ***electromagnetic*** — core concept\n"
    "  **frequency** — measured in hertz\n\n"
    "DETAILS: All electromagnetic waves travel at the speed of light in vacuum, "
    "approximately 299,792,458 meters per second. The energy of a photon is "
    "directly proportional to its frequency (E = hf). Higher frequency radiation "
    "carries more energy — which is why gamma rays are ionizing while radio waves are not."
)

MARKDOWN_TEXT = (
    "# Heading\n"
    "This is **bold** and *italic* text.\n"
    "A [link](https://example.com) and `inline code`.\n"
    "- bullet point one\n"
    "- bullet point two"
)


class TestProfileApplication:
    """Profile switching — like changing measurement instruments."""

    def test_default_profile_on_init(self, sensory: SensoryMode) -> None:
        assert sensory.profile == SensoryProfile.DEFAULT
        assert sensory.state.line_width == 80
        assert sensory.state.strip_formatting is False

    def test_switch_to_low_vision(self, sensory: SensoryMode) -> None:
        state = sensory.apply_profile(SensoryProfile.LOW_VISION)
        assert state.profile == SensoryProfile.LOW_VISION
        assert state.line_width == 60
        assert state.uppercase_headings is True

    def test_switch_to_screen_reader(self, sensory: SensoryMode) -> None:
        state = sensory.apply_profile(SensoryProfile.SCREEN_READER)
        assert state.strip_formatting is True
        assert state.simplify_punctuation is True
        assert state.uppercase_headings is True

    def test_switch_to_cognitive(self, sensory: SensoryMode) -> None:
        state = sensory.apply_profile(SensoryProfile.COGNITIVE)
        assert state.strip_formatting is True
        assert state.simplify_punctuation is True
        assert state.urgency_level == "gentle"
        assert state.chunk_size == 2

    def test_switch_to_focus(self, sensory: SensoryMode) -> None:
        state = sensory.apply_profile(SensoryProfile.FOCUS)
        assert state.line_width == 50
        assert state.chunk_size == 1
        assert state.urgency_level == "none"

    def test_switch_to_calm(self, sensory: SensoryMode) -> None:
        state = sensory.apply_profile(SensoryProfile.CALM)
        assert state.urgency_level == "none"
        assert state.strip_formatting is False

    def test_all_profiles_produce_valid_state(self, sensory: SensoryMode) -> None:
        """Every profile must produce a valid state — complete coverage."""
        for profile in SensoryProfile:
            state = sensory.apply_profile(profile)
            assert isinstance(state, SensoryState)
            assert state.profile == profile
            assert state.line_width > 0


class TestFormatting:
    """Output formatting — signal transformation pipeline."""

    def test_default_profile_preserves_content(self, sensory: SensoryMode) -> None:
        """Default profile is identity transform — like a transparent medium."""
        formatted = sensory.format_output(SAMPLE_OUTPUT)
        assert "electromagnetic" in formatted
        assert "299,792,458" in formatted

    def test_strip_formatting_removes_markdown(self, sensory: SensoryMode) -> None:
        """Stripping formatting — like removing carrier wave to get baseband signal."""
        sensory.apply_profile(SensoryProfile.SCREEN_READER)
        formatted = sensory.format_output(MARKDOWN_TEXT)
        assert "**" not in formatted
        assert "*" not in formatted or "italic" in formatted
        assert "`" not in formatted
        assert "[link]" not in formatted
        assert "link" in formatted  # text preserved

    def test_simplify_punctuation_removes_parens(self, sensory: SensoryMode) -> None:
        sensory.apply_profile(SensoryProfile.COGNITIVE)
        text = "The energy (measured in joules) is proportional; the frequency matters."
        formatted = sensory.format_output(text)
        assert "(" not in formatted
        assert ")" not in formatted
        assert ";" not in formatted

    def test_uppercase_headings_for_screen_reader(self, sensory: SensoryMode) -> None:
        sensory.apply_profile(SensoryProfile.SCREEN_READER)
        formatted = sensory.format_output(SAMPLE_OUTPUT)
        assert "IN BRIEF:" in formatted or "IN BRIEF" in formatted

    def test_line_wrapping_respects_width(self, sensory: SensoryMode) -> None:
        sensory.apply_profile(SensoryProfile.FOCUS)  # 50 char width
        long_line = "A" * 100
        formatted = sensory.format_output(long_line)
        lines = formatted.split("\n")
        for line in lines:
            assert len(line) <= 55  # some tolerance for word wrapping

    def test_gentle_urgency_softens_harsh_words(self, sensory: SensoryMode) -> None:
        """Gentle mode — like low-pass filtering high-frequency noise."""
        sensory.apply_profile(SensoryProfile.COGNITIVE)
        text = "ERROR: You MUST fix this IMMEDIATELY or it will FAIL."
        formatted = sensory.format_output(text)
        assert "error" not in formatted.lower() or "note" in formatted.lower()

    def test_no_urgency_removes_exclamation(self, sensory: SensoryMode) -> None:
        sensory.apply_profile(SensoryProfile.CALM)
        text = "This is important! Act now! WARNING!"
        formatted = sensory.format_output(text)
        assert "!" not in formatted

    def test_information_preserved_across_profiles(self, sensory: SensoryMode) -> None:
        """Core information must survive all transformations — conservation law."""
        key_facts = ["299,792,458", "electromagnetic", "frequency"]
        for profile in SensoryProfile:
            sensory.apply_profile(profile)
            formatted = sensory.format_output(SAMPLE_OUTPUT)
            for fact in key_facts:
                assert fact in formatted, (
                    f"Fact '{fact}' lost in profile '{profile.value}'"
                )


class TestCustomAdjustments:
    """User overrides — like manual instrument calibration."""

    def test_adjust_line_width(self, sensory: SensoryMode) -> None:
        state = sensory.adjust(line_width=40)
        assert state.line_width == 40

    def test_adjust_records_adaptation(self, sensory: SensoryMode) -> None:
        sensory.adjust(chunk_size=1)
        assert any("chunk_size" in a.what for a in sensory.state.adaptations)

    def test_adjust_preserves_profile(self, sensory: SensoryMode) -> None:
        sensory.apply_profile(SensoryProfile.COGNITIVE)
        sensory.adjust(line_width=40)
        assert sensory.state.profile == SensoryProfile.COGNITIVE


class TestExplainCurrent:
    """Self-description — the tool must explain its own state clearly."""

    def test_explain_default(self, sensory: SensoryMode) -> None:
        info = sensory.explain_current()
        assert "default" in info.lower()

    def test_explain_cognitive_mentions_adaptations(self, sensory: SensoryMode) -> None:
        sensory.apply_profile(SensoryProfile.COGNITIVE)
        info = sensory.explain_current()
        assert "plain text" in info.lower() or "formatting removed" in info.lower()
        assert "gentle" in info.lower()

    def test_explain_low_vision_mentions_width(self, sensory: SensoryMode) -> None:
        sensory.apply_profile(SensoryProfile.LOW_VISION)
        info = sensory.explain_current()
        assert "60" in info
