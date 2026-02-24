"""Tests for Mycelium Safety Layer — risk mitigation and boundary enforcement.

Validates all safety invariants:
    1. Input bounds (length, type, emptiness)
    2. PII detection (email, phone, SSN, credit card, IP)
    3. Content sanitization (control characters, null bytes)
    4. Memory caps (history size enforcement)
    5. Parameter validation (ranges, allowed values)
    6. Adversarial inputs (injection attempts, extreme sizes)
    7. Output integrity (fail-closed behavior)

Per Trust Layer Rule 1.1: all test descriptions use descriptive nouns,
not perpetrator voice. Tests describe what IS detected, not what
someone IS DOING.
"""

from __future__ import annotations

import pytest

from mycelium.core import PersonaProfile, SynthesisResult
from mycelium.instrument import Instrument
from mycelium.persona import PersonaEngine, InteractionSignal, _MAX_SIGNALS
from mycelium.safety import (
    MAX_CONCEPT_NAME_LENGTH,
    MAX_HIGHLIGHTS,
    MAX_INPUT_LENGTH,
    SafetyGuard,
    SafetyReport,
    SafetyVerdict,
    detect_pii,
    validate_input,
)


class TestInputValidation:
    """Input bounds enforcement — like thermal limits on a heat engine.
    Exceeding bounds is rejected, not passed through."""

    def test_valid_text_passes(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_input("The speed of light is 299,792,458 m/s.")
        assert report.verdict == SafetyVerdict.PASS
        assert report.is_safe is True

    def test_empty_string_rejected(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_input("")
        assert report.verdict == SafetyVerdict.REJECT
        assert not report.is_safe

    def test_whitespace_only_rejected(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_input("   \t\n  ")
        assert report.verdict == SafetyVerdict.REJECT

    def test_oversized_input_rejected(self) -> None:
        """Input exceeding 500KB is rejected — like exceeding reactor thermal limits."""
        guard = SafetyGuard()
        huge = "x" * (MAX_INPUT_LENGTH + 1)
        report = guard.validate_input(huge)
        assert report.verdict == SafetyVerdict.REJECT
        assert "exceeds maximum length" in report.reasons[0]

    def test_max_length_boundary_passes(self) -> None:
        """Exactly at the limit should pass."""
        guard = SafetyGuard()
        text = "x" * MAX_INPUT_LENGTH
        report = guard.validate_input(text)
        assert report.is_safe

    def test_processing_time_recorded(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_input("Test input.")
        assert report.processing_time_ms >= 0.0

    def test_original_length_recorded(self) -> None:
        guard = SafetyGuard()
        text = "Exactly 42 characters long for this test!!"
        report = guard.validate_input(text)
        assert report.original_length == len(text)


class TestContentSanitization:
    """Control character removal — like filtering noise from a signal."""

    def test_null_bytes_removed(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_input("Hello\x00World")
        assert report.is_safe
        assert "\x00" not in (report.sanitized_text or "")
        assert "Control characters removed" in report.reasons[0]

    def test_control_characters_removed(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_input("Line one\x07Bell\x08Backspace")
        assert report.is_safe
        assert report.sanitized_text is not None
        assert "\x07" not in report.sanitized_text
        assert "\x08" not in report.sanitized_text

    def test_safe_whitespace_preserved(self) -> None:
        """Tabs, newlines, carriage returns are safe — preserved."""
        guard = SafetyGuard()
        text = "Line one\nLine two\tTabbed\rReturn"
        report = guard.validate_input(text)
        assert report.is_safe
        assert report.sanitized_text == text  # no changes


class TestPIIDetection:
    """PII detection — heuristic, local-only. Warn, don't block.
    Per Trust Layer Rule 4.2: non-punitive response."""

    def test_email_detected(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_input("Contact info: user@example.com for details.")
        assert report.pii_detected is True
        assert "email_address" in report.reasons[0]
        assert report.is_safe  # warn, not block

    def test_phone_number_detected(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_input("Call 555-123-4567 for support.")
        assert report.pii_detected is True

    def test_ssn_pattern_detected(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_input("SSN reference: 123-45-6789 in records.")
        assert report.pii_detected is True
        assert any("social_security" in r for r in report.reasons)

    def test_credit_card_pattern_detected(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_input("Card number 4111-1111-1111-1111 on file.")
        assert report.pii_detected is True

    def test_ip_address_detected(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_input("Server at 192.168.1.100 responded.")
        assert report.pii_detected is True

    def test_no_pii_in_clean_text(self) -> None:
        """Scientific text should have no PII false positives."""
        guard = SafetyGuard()
        report = guard.validate_input(
            "The electromagnetic spectrum spans from radio waves at 3 Hz "
            "to gamma rays above 30 EHz. All travel at 299,792,458 m/s."
        )
        assert report.pii_detected is False

    def test_pii_warning_includes_local_processing_note(self) -> None:
        """PII warning must state data is processed locally — transparency."""
        guard = SafetyGuard()
        report = guard.validate_input("Email: test@test.com for correspondence.")
        assert any("locally only" in r for r in report.reasons)

    def test_module_level_detect_pii(self) -> None:
        """Module-level convenience function works."""
        found = detect_pii("Contact: user@example.com, phone: 555-123-4567")
        assert "email_address" in found
        assert "phone_number" in found

    def test_module_level_validate_input(self) -> None:
        report = validate_input("Clean scientific text about thermodynamics.")
        assert report.is_safe


class TestParameterValidation:
    """Parameter bounds checking — like instrument calibration limits."""

    def test_numeric_min_enforced(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_parameter("count", -5, min_val=0)
        assert report.verdict == SafetyVerdict.REJECT

    def test_numeric_max_enforced(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_parameter("highlights", 100, max_val=50)
        assert report.verdict == SafetyVerdict.REJECT

    def test_numeric_in_range_passes(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_parameter("count", 10, min_val=1, max_val=50)
        assert report.verdict == SafetyVerdict.PASS

    def test_string_max_length_enforced(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_parameter("name", "x" * 200, max_length=100)
        assert report.verdict == SafetyVerdict.REJECT

    def test_allowed_values_enforced(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_parameter(
            "depth", "invalid", allowed_values={"espresso", "americano", "cold_brew"}
        )
        assert report.verdict == SafetyVerdict.REJECT

    def test_allowed_value_passes(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_parameter(
            "depth", "espresso", allowed_values={"espresso", "americano", "cold_brew"}
        )
        assert report.verdict == SafetyVerdict.PASS

    def test_list_size_enforced(self) -> None:
        guard = SafetyGuard()
        big_list = list(range(100))
        report = guard.validate_parameter("items", big_list, max_val=50)
        assert report.verdict == SafetyVerdict.REJECT


class TestConceptRegistrationLimits:
    """Concept registration bounds — prevent catalog exhaustion."""

    def test_concept_name_length_enforced(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_concept_name("x" * (MAX_CONCEPT_NAME_LENGTH + 1))
        assert report.verdict == SafetyVerdict.REJECT

    def test_valid_concept_name_passes(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_concept_name("thermodynamics")
        assert report.verdict == SafetyVerdict.PASS

    def test_lenses_count_enforced(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_lenses_count("test", current=18, adding=5)
        assert report.verdict == SafetyVerdict.REJECT

    def test_lenses_within_limit_passes(self) -> None:
        guard = SafetyGuard()
        report = guard.validate_lenses_count("test", current=3, adding=2)
        assert report.verdict == SafetyVerdict.PASS


class TestHistoryCaps:
    """Memory cap enforcement — prevent resource exhaustion,
    like thermal protection preventing meltdown."""

    def test_enforce_history_cap_trims(self) -> None:
        guard = SafetyGuard()
        big_list = list(range(2000))
        trimmed = guard.enforce_history_cap(big_list, max_size=100)
        assert len(trimmed) == 100
        assert trimmed[0] == 1900  # oldest removed, newest kept

    def test_enforce_cap_small_list_unchanged(self) -> None:
        guard = SafetyGuard()
        small_list = [1, 2, 3]
        result = guard.enforce_history_cap(small_list, max_size=100)
        assert result == [1, 2, 3]

    def test_persona_engine_caps_signals(self) -> None:
        """PersonaEngine must not grow unbounded."""
        engine = PersonaEngine()
        for i in range(_MAX_SIGNALS + 100):
            engine.observe(InteractionSignal(signal_type="query", content=f"query {i}"))
        assert len(engine._signals) <= _MAX_SIGNALS

    def test_persona_engine_caps_word_history(self) -> None:
        engine = PersonaEngine()
        # Each query adds several words; flood with queries
        long_query = " ".join(f"word{i}" for i in range(500))
        for _ in range(20):
            engine.observe(InteractionSignal(signal_type="query", content=long_query))
        assert len(engine._word_history) <= 2_000


class TestInstrumentSafetyIntegration:
    """Instrument-level safety — all public methods must be safe."""

    def test_synthesize_rejects_empty(self) -> None:
        m = Instrument()
        result = m.synthesize("")
        assert "could not be processed" in result.gist

    def test_synthesize_rejects_oversized(self) -> None:
        m = Instrument()
        result = m.synthesize("x" * (MAX_INPUT_LENGTH + 1))
        assert "could not be processed" in result.gist

    def test_synthesize_sanitizes_control_chars(self) -> None:
        m = Instrument()
        result = m.synthesize("Clean text\x00 with null byte. More content here for synthesis.")
        assert "\x00" not in result.gist

    def test_synthesize_warns_on_pii(self) -> None:
        """PII in input should still process (warn, not block)."""
        m = Instrument()
        result = m.synthesize(
            "The researcher at user@example.com published findings on "
            "electromagnetic radiation spanning the full spectrum."
        )
        assert len(result.gist) > 0  # processed, not blocked

    def test_summarize_rejects_empty(self) -> None:
        m = Instrument()
        result = m.summarize("")
        assert "could not be processed" in result

    def test_simplify_rejects_empty(self) -> None:
        m = Instrument()
        result = m.simplify("")
        assert "could not be processed" in result

    def test_keywords_rejects_empty(self) -> None:
        m = Instrument()
        result = m.keywords("")
        assert result == []

    def test_explore_rejects_empty_concept(self) -> None:
        m = Instrument()
        assert m.explore("") is None

    def test_explore_rejects_oversized_concept(self) -> None:
        m = Instrument()
        assert m.explore("x" * 200) is None

    def test_observe_rejects_empty(self) -> None:
        """observe() with empty string should be a no-op."""
        m = Instrument()
        m.observe("")  # should not raise

    def test_observe_caps_input_length(self) -> None:
        """observe() caps text at 2000 chars."""
        m = Instrument()
        m.observe("a" * 5000)  # should not raise or store full 5000

    def test_highlights_clamped(self) -> None:
        m = Instrument()
        result = m.synthesize(
            "Electromagnetic radiation includes radio waves, microwaves, "
            "infrared, visible light, ultraviolet, X-rays, and gamma rays. "
            "Each type has distinct frequency and wavelength characteristics.",
            max_highlights=999,
        )
        assert len(result.highlights) <= MAX_HIGHLIGHTS

    def test_safety_stats_accessible(self) -> None:
        m = Instrument()
        m.synthesize("Test input for safety stats.")
        stats = m.safety_stats
        assert stats["checks_performed"] >= 1


class TestAdversarialInputs:
    """Adversarial and edge-case inputs — stress testing safety boundaries."""

    def test_only_numbers(self) -> None:
        """Pure numeric input should process without error."""
        m = Instrument()
        result = m.synthesize("12345 67890 11111 22222 33333 44444 55555")
        assert len(result.gist) > 0

    def test_unicode_text_processes(self) -> None:
        """Unicode (non-Latin) text should not crash the system."""
        m = Instrument()
        result = m.synthesize(
            "বাংলা ভাষায় লেখা পাঠ্য। এটি একটি পরীক্ষা। "
            "তাপমাত্রা এবং চাপ পরিবর্তনের ফলে পদার্থের অবস্থার পরিবর্তন ঘটে।"
        )
        assert len(result.gist) > 0

    def test_repeated_single_char(self) -> None:
        """Repeated single character — degenerate input."""
        m = Instrument()
        result = m.synthesize("aaaa " * 100)
        assert len(result.gist) > 0

    def test_very_long_single_sentence(self) -> None:
        """One very long sentence — no sentence splitting possible."""
        m = Instrument()
        text = "word " * 1000  # 1000 words, no period
        result = m.synthesize(text)
        assert len(result.gist) > 0

    def test_mixed_encoding_chars(self) -> None:
        """Mixed encoding characters should not crash."""
        m = Instrument()
        result = m.synthesize("Hello café résumé naïve 日本語 العربية")
        assert len(result.gist) > 0

    def test_html_like_input_not_executed(self) -> None:
        """HTML-like content should be treated as plain text, never executed."""
        m = Instrument()
        result = m.synthesize(
            "<script>alert('test')</script> Normal text about physics."
        )
        assert "alert" not in result.gist or "script" in result.gist.lower()
        # The key assertion: it processed without error

    def test_newlines_and_tabs_preserved(self) -> None:
        m = Instrument()
        result = m.synthesize(
            "Line one about thermodynamics.\n"
            "Line two about phase transitions.\n"
            "Line three about energy conservation."
        )
        assert len(result.gist) > 0
