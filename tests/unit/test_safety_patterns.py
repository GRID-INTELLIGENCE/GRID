"""
Unit tests for the safety detection lexicon (patterns.py) and its
integration with the ContentModerator in framework.py.

Validates:
  - Seed set integrity (count, categories, confidence tiers)
  - No false positives on benign content
  - Detection of actual harmful tokens
  - Confidence tier propagation into SafetyViolation
  - No verbs, no targeting pronouns, no everyday words in the lexicon
"""

from __future__ import annotations

import importlib.util
import os
import sys

# ── Direct file-based imports ────────────────────────────────────────────
# Root-level security/ package shadows src/security/, so we load by path.
_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "src")


def _load_module(name: str, rel_path: str):
    """Load a module by file path to avoid package shadowing."""
    path = os.path.normpath(os.path.join(_SRC, rel_path))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_patterns = _load_module("_safety_patterns", "security/ai_safety/patterns.py")

# Build a synthetic package so framework.py's `from .patterns import ...` works.
import types

_ai_safety_dir = os.path.normpath(os.path.join(_SRC, "security", "ai_safety"))

_sec_pkg = types.ModuleType("security")
_sec_pkg.__path__ = [os.path.normpath(os.path.join(_SRC, "security"))]
_sec_pkg.__package__ = "security"

_ai_pkg = types.ModuleType("security.ai_safety")
_ai_pkg.__path__ = [_ai_safety_dir]
_ai_pkg.__package__ = "security.ai_safety"

_patterns.__name__ = "security.ai_safety.patterns"
_patterns.__package__ = "security.ai_safety"

sys.modules["security"] = _sec_pkg
sys.modules["security.ai_safety"] = _ai_pkg
sys.modules["security.ai_safety.patterns"] = _patterns


# ── patterns.py unit tests ───────────────────────────────────────────────


class TestSeedSetIntegrity:
    """The seed set must be small, all HIGH, and structurally correct."""

    def test_token_count(self):
        assert _patterns.get_pattern_count() == 15

    def test_all_categories_present(self):
        expected = {
            "nonconsensual_media",
            "platform_exploitation",
            "financial_fraud",
            "violence",
            "gendered_violence",
            "distress_signals",
        }
        assert set(_patterns.get_all_categories()) == expected

    def test_all_tokens_are_high_confidence(self):
        for category, entries in _patterns.HARMFUL_PATTERNS.items():
            for token, confidence in entries:
                assert confidence == "high", (
                    f"Seed token '{token}' in '{category}' has confidence '{confidence}' — seed set must be all HIGH"
                )

    def test_no_duplicate_tokens(self):
        seen = set()
        for token in _patterns.ALL_TOKENS:
            assert token not in seen, f"Duplicate token: '{token}'"
            seen.add(token)

    def test_flattened_lookups_consistent(self):
        total = sum(len(e) for e in _patterns.HARMFUL_PATTERNS.values())
        assert len(_patterns.ALL_TOKENS) == total
        assert len(_patterns.TOKEN_CONFIDENCE) == total
        assert len(_patterns.TOKEN_CATEGORY) == total


class TestTokenQuality:
    """Every token must be a bare noun — no verbs, no pronouns, no sentences."""

    def test_no_cholito_verb_endings(self):
        """Cholito verb endings should not appear as suffixes."""
        cholito_endings = ("করব", "বানাব", "দেব", "মারব", "করো", "বানাও", "দাও")
        for token in _patterns.ALL_TOKENS:
            for ending in cholito_endings:
                assert not token.endswith(ending), f"Token '{token}' ends with Cholito verb form '{ending}'"

    def test_no_targeting_pronouns(self):
        """No second-person targeting pronouns."""
        pronouns = ("তোর", "তোকে", "তুই", "তুমি", "আমি", "আমার")
        for token in _patterns.ALL_TOKENS:
            for pronoun in pronouns:
                assert pronoun not in token, f"Token '{token}' contains targeting pronoun '{pronoun}'"


class TestCheckContent:
    """check_content must detect harmful tokens and ignore benign text."""

    def test_detects_known_token(self):
        results = _patterns.check_content("সেক্সটর্শন")
        assert len(results) == 1
        assert results[0]["token"] == "সেক্সটর্শন"
        assert results[0]["category"] == "nonconsensual_media"
        assert results[0]["confidence"] == "high"

    def test_no_match_on_benign_bangla(self):
        benign = "আমি আজ সকালে চা খেয়েছি এবং অফিসে গেছি"
        assert _patterns.check_content(benign) == []

    def test_no_match_on_benign_english(self):
        assert _patterns.check_content("Good morning, how are you today?") == []

    def test_no_match_on_common_words(self):
        """Words we deliberately excluded must NOT match."""
        false_positive_bait = [
            "ভাইরাল ভিডিও দেখেছো?",
            "ওটিপি দিয়ে লগইন করুন",
            "স্ক্রিনশট নিয়েছি",
            "পিন নম্বর ভুলে গেছি",
            "আমি খুব হতাশ আজকে",
            "একাকীত্ব অনুভব করছি",
        ]
        for text in false_positive_bait:
            results = _patterns.check_content(text)
            assert results == [], f"False positive on: '{text}' → {results}"

    def test_detects_distress_signal(self):
        results = _patterns.check_content("আত্মহত্যা")
        assert len(results) == 1
        assert results[0]["category"] == "distress_signals"

    def test_multiple_tokens_detected(self):
        text = "ফিশিং এবং জালিয়াতি"
        results = _patterns.check_content(text)
        assert len(results) == 2
        categories = {r["category"] for r in results}
        assert "financial_fraud" in categories


class TestGetPatternsByCategory:
    def test_returns_tokens_for_valid_category(self):
        tokens = _patterns.get_patterns_by_category("distress_signals")
        assert len(tokens) == 3
        assert "আত্মহত্যা" in tokens

    def test_returns_empty_for_unknown_category(self):
        assert _patterns.get_patterns_by_category("nonexistent") == []


# ── framework.py integration tests ──────────────────────────────────────

import asyncio

_fw_path = os.path.normpath(os.path.join(_SRC, "security/ai_safety/framework.py"))
_fw_spec = importlib.util.spec_from_file_location(
    "security.ai_safety.framework",
    _fw_path,
    submodule_search_locations=[],
)
_framework = importlib.util.module_from_spec(_fw_spec)
_framework.__package__ = "security.ai_safety"
sys.modules["security.ai_safety.framework"] = _framework
_fw_spec.loader.exec_module(_framework)


def _run(coro):
    """Run async coroutine synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestFrameworkSafetyPatterns:
    """ContentModerator._check_safety_patterns integrates with patterns.py."""

    def test_moderator_loads_patterns(self):
        moderator = _framework.ContentModerator()
        assert len(moderator.safety_patterns) == 6

    def test_moderator_detects_harmful_token(self):
        moderator = _framework.ContentModerator()
        violations = _run(moderator.analyze_content("সেক্সটর্শন"))
        safety_hits = [v for v in violations if v.evidence and v.evidence.get("confidence_tier") == "high"]
        assert len(safety_hits) >= 1

    def test_moderator_no_violation_on_benign(self):
        moderator = _framework.ContentModerator()
        violations = _run(moderator.analyze_content("আজকের আবহাওয়া খুব সুন্দর"))
        safety_hits = [v for v in violations if v.evidence and "confidence_tier" in v.evidence]
        assert safety_hits == []

    def test_distress_signal_severity_is_high(self):
        moderator = _framework.ContentModerator()
        violations = _run(moderator.analyze_content("আত্মহত্যা"))
        ds = [v for v in violations if v.evidence and v.evidence.get("category") == "distress_signals"]
        assert len(ds) >= 1
        assert ds[0].severity == _framework.ThreatLevel.HIGH

    def test_violence_severity_is_critical(self):
        moderator = _framework.ContentModerator()
        violations = _run(moderator.analyze_content("গণহত্যা"))
        vl = [v for v in violations if v.evidence and v.evidence.get("category") == "violence"]
        assert len(vl) >= 1
        assert vl[0].severity == _framework.ThreatLevel.CRITICAL

    def test_financial_fraud_severity_is_medium(self):
        moderator = _framework.ContentModerator()
        violations = _run(moderator.analyze_content("ফিশিং"))
        ff = [v for v in violations if v.evidence and v.evidence.get("category") == "financial_fraud"]
        assert len(ff) >= 1
        assert ff[0].severity == _framework.ThreatLevel.MEDIUM

    def test_confidence_score_is_09_for_high_tier(self):
        moderator = _framework.ContentModerator()
        violations = _run(moderator.analyze_content("লিঞ্চিং"))
        hits = [x for x in violations if x.evidence and x.evidence.get("confidence_tier") == "high"]
        assert len(hits) >= 1
        assert hits[0].confidence == 0.9
