"""
Unit tests for PII masking strategies and MaskingEngine.

Covers: all 6 strategies, MaskingEngine.mask_text/mask_single,
compliance presets, and original_hash verification.
"""

from __future__ import annotations

import hashlib

import pytest

from safety.privacy.core.masking import (
    AuditStrategy,
    CompliancePreset,
    HashStrategy,
    MaskingEngine,
    MaskStrategyType,
    NoopStrategy,
    PartialMaskStrategy,
    RedactStrategy,
    TokenizeStrategy,
    _hash_value,
    create_compliance_engine,
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _expected_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# _hash_value
# ---------------------------------------------------------------------------

class TestHashValue:
    def test_deterministic(self):
        assert _hash_value("hello") == _hash_value("hello")

    def test_length(self):
        assert len(_hash_value("test")) == 16

    def test_different_inputs(self):
        assert _hash_value("a") != _hash_value("b")


# ---------------------------------------------------------------------------
# RedactStrategy
# ---------------------------------------------------------------------------

class TestRedactStrategy:
    def test_redacts_to_type_label(self):
        result = RedactStrategy().mask("john@example.com", "EMAIL")
        assert result.masked == "[EMAIL]"
        assert result.strategy_used == MaskStrategyType.REDACT

    def test_original_hash_not_plaintext(self):
        value = "secret@email.com"
        result = RedactStrategy().mask(value, "EMAIL")
        assert result.original_hash == _expected_hash(value)
        assert value not in result.original_hash

    def test_replacements_populated(self):
        result = RedactStrategy().mask("test", "NAME")
        assert len(result.replacements) == 1
        assert result.replacements[0]["type"] == "NAME"


# ---------------------------------------------------------------------------
# PartialMaskStrategy
# ---------------------------------------------------------------------------

class TestPartialMaskStrategy:
    def test_email_partial_mask(self):
        result = PartialMaskStrategy().mask("john@example.com", "EMAIL")
        assert "@example.com" in result.masked
        assert result.masked.startswith("joh")
        assert "*" in result.masked

    def test_phone_last_four(self):
        result = PartialMaskStrategy().mask("+15551234567", "PHONE")
        assert result.masked.endswith("4567")
        assert result.masked.startswith("*")

    def test_short_value_falls_back_to_redact(self):
        result = PartialMaskStrategy(reveal_chars=3).mask("ab", "NAME")
        assert result.masked == "[NAME]"
        assert result.strategy_used == MaskStrategyType.REDACT

    def test_default_masking(self):
        result = PartialMaskStrategy().mask("SomeValue", "CUSTOM")
        assert result.masked[0] == "S"
        assert result.masked[-1] == "e"
        assert "*" in result.masked

    def test_short_default_fully_masked(self):
        result = PartialMaskStrategy().mask("abcd", "CUSTOM")
        assert result.masked == "****"


# ---------------------------------------------------------------------------
# HashStrategy
# ---------------------------------------------------------------------------

class TestHashStrategy:
    def test_hash_format(self):
        result = HashStrategy().mask("secret", "PASSWORD")
        assert result.masked.startswith("[PASSWORD_HASH:")
        assert result.masked.endswith("]")

    def test_salted_hash_differs(self):
        unsalted = HashStrategy().mask("value", "X")
        salted = HashStrategy(salt="pepper").mask("value", "X")
        assert unsalted.masked != salted.masked

    def test_original_hash_set(self):
        result = HashStrategy().mask("mypassword", "PASSWORD")
        assert result.original_hash == _expected_hash("mypassword")


# ---------------------------------------------------------------------------
# TokenizeStrategy
# ---------------------------------------------------------------------------

class TestTokenizeStrategy:
    def test_token_format(self):
        strategy = TokenizeStrategy()
        result = strategy.mask("test@email.com", "EMAIL")
        assert result.masked.startswith("[EMAIL_TOKEN:")
        assert result.masked.endswith("]")

    def test_consistent_token(self):
        strategy = TokenizeStrategy()
        r1 = strategy.mask("same_value", "NAME")
        r2 = strategy.mask("same_value", "NAME")
        assert r1.masked == r2.masked

    def test_different_values_different_tokens(self):
        strategy = TokenizeStrategy()
        r1 = strategy.mask("alice", "NAME")
        r2 = strategy.mask("bob", "NAME")
        assert r1.masked != r2.masked

    def test_replacement_has_original_hash(self):
        strategy = TokenizeStrategy()
        result = strategy.mask("data", "TYPE")
        assert "original_hash" in result.replacements[0]


# ---------------------------------------------------------------------------
# AuditStrategy
# ---------------------------------------------------------------------------

class TestAuditStrategy:
    def test_audit_ref_format(self):
        strategy = AuditStrategy()
        result = strategy.mask("secret_data", "SSN")
        assert result.masked.startswith("[SSN_AUDIT:REF-")
        assert result.masked.endswith("]")

    def test_incrementing_counter(self):
        strategy = AuditStrategy()
        r1 = strategy.mask("a", "X")
        r2 = strategy.mask("b", "X")
        assert "00000001" in r1.masked
        assert "00000002" in r2.masked

    def test_replacement_has_original_hash(self):
        strategy = AuditStrategy()
        result = strategy.mask("pii", "TYPE")
        assert "original_hash" in result.replacements[0]


# ---------------------------------------------------------------------------
# NoopStrategy
# ---------------------------------------------------------------------------

class TestNoopStrategy:
    def test_value_unchanged(self):
        result = NoopStrategy().mask("visible", "TEST")
        assert result.masked == "visible"
        assert result.replacements == []
        assert result.strategy_used == MaskStrategyType.NOOP


# ---------------------------------------------------------------------------
# MaskingEngine
# ---------------------------------------------------------------------------

class TestMaskingEngine:
    def test_mask_text_no_detections(self):
        engine = MaskingEngine()
        result = engine.mask_text("Hello world", [])
        assert result.masked == "Hello world"

    def test_mask_text_single_detection(self):
        engine = MaskingEngine()
        text = "Contact john@example.com please"
        detections = [
            {"pii_type": "EMAIL", "start": 8, "end": 24, "value": "john@example.com"},
        ]
        result = engine.mask_text(text, detections)
        assert "[EMAIL]" in result.masked
        assert "john@example.com" not in result.masked

    def test_mask_text_multiple_detections(self):
        engine = MaskingEngine()
        text = "Name: Alice, Phone: 555-1234"
        detections = [
            {"pii_type": "NAME", "start": 6, "end": 11, "value": "Alice"},
            {"pii_type": "PHONE", "start": 20, "end": 28, "value": "555-1234"},
        ]
        result = engine.mask_text(text, detections)
        assert "Alice" not in result.masked
        assert "555-1234" not in result.masked

    def test_mask_single(self):
        engine = MaskingEngine()
        result = engine.mask_single("secret", "PASSWORD")
        assert result.masked == "[PASSWORD]"

    def test_strategy_override(self):
        engine = MaskingEngine(
            strategy_overrides={"EMAIL": MaskStrategyType.PARTIAL},
        )
        result = engine.mask_single("john@example.com", "EMAIL")
        # Should use partial, not redact
        assert "@" in result.masked  # Partial keeps domain
        assert result.strategy_used == MaskStrategyType.PARTIAL

    def test_out_of_bounds_detection_skipped(self):
        engine = MaskingEngine()
        text = "short"
        detections = [
            {"pii_type": "X", "start": 100, "end": 110, "value": "phantom"},
        ]
        result = engine.mask_text(text, detections)
        assert result.masked == "short"


# ---------------------------------------------------------------------------
# Compliance presets
# ---------------------------------------------------------------------------

class TestCompliancePresets:
    def test_gdpr_engine_uses_partial_for_email(self):
        engine = create_compliance_engine(CompliancePreset.GDPR)
        result = engine.mask_single("user@domain.com", "EMAIL")
        assert "@" in result.masked  # Partial preserves domain

    def test_hipaa_engine_uses_audit_for_ssn(self):
        engine = create_compliance_engine(CompliancePreset.HIPAA)
        result = engine.mask_single("123-45-6789", "SSN")
        assert "AUDIT" in result.masked

    def test_pci_dss_partial_card(self):
        engine = create_compliance_engine(CompliancePreset.PCI_DSS)
        result = engine.mask_single("4111111111111111", "CREDIT_CARD")
        # CREDIT_CARD uses default partial: first char + *** + last char
        assert result.strategy_used == MaskStrategyType.PARTIAL
        assert "*" in result.masked

    def test_custom_overrides(self):
        engine = create_compliance_engine(
            CompliancePreset.GDPR,
            custom_overrides={"EMAIL": MaskStrategyType.REDACT},
        )
        result = engine.mask_single("x@y.com", "EMAIL")
        assert result.masked == "[EMAIL]"


# ---------------------------------------------------------------------------
# Verify original_hash contains hash, not plaintext
# ---------------------------------------------------------------------------

class TestOriginalHashIntegrity:
    """Ensure no MaskResult stores plaintext PII in original_hash."""

    @pytest.mark.parametrize("strategy_cls", [
        RedactStrategy,
        HashStrategy,
        TokenizeStrategy,
        AuditStrategy,
        NoopStrategy,
    ])
    def test_no_plaintext_in_original_hash(self, strategy_cls):
        value = "sensitive_pii_value"
        result = strategy_cls().mask(value, "TEST")
        assert result.original_hash != value
        assert result.original_hash == _expected_hash(value)

    def test_partial_mask_no_plaintext(self):
        value = "longvalue@example.com"
        result = PartialMaskStrategy().mask(value, "EMAIL")
        assert result.original_hash != value
        assert result.original_hash == _expected_hash(value)

    def test_engine_mask_text_no_plaintext(self):
        engine = MaskingEngine()
        text = "Call me at 555-0100"
        detections = [{"pii_type": "PHONE", "start": 11, "end": 19, "value": "555-0100"}]
        result = engine.mask_text(text, detections)
        assert result.original_hash != text
        assert result.original_hash == _expected_hash(text)
