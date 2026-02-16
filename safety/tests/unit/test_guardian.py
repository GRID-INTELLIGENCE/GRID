"""
Unit tests for the GUARDIAN rule engine.

Covers: evaluate, quick_check, cache, singleton identity, thread safety.
"""

from __future__ import annotations

import threading

from safety.guardian.engine import (
    GuardianEngine,
    MatchType,
    RuleAction,
    SafetyRule,
    Severity,
    get_guardian_engine,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_engine(*rules: SafetyRule) -> GuardianEngine:
    """Create a fresh GuardianEngine loaded with the given rules."""
    engine = GuardianEngine(enable_cache=True)
    engine.load_rules(list(rules))
    return engine


def _keyword_rule(
    rule_id: str = "test-kw",
    keywords: list[str] | None = None,
    severity: Severity = Severity.HIGH,
    action: RuleAction = RuleAction.BLOCK,
) -> SafetyRule:
    return SafetyRule(
        id=rule_id,
        name=f"Test keyword rule {rule_id}",
        description="test",
        category="test",
        severity=severity,
        action=action,
        match_type=MatchType.KEYWORD,
        keywords=keywords or ["forbidden_word"],
        confidence=0.9,
    )


def _regex_rule(
    rule_id: str = "test-rx",
    patterns: list[str] | None = None,
    severity: Severity = Severity.HIGH,
    action: RuleAction = RuleAction.BLOCK,
) -> SafetyRule:
    return SafetyRule(
        id=rule_id,
        name=f"Test regex rule {rule_id}",
        description="test",
        category="test",
        severity=severity,
        action=action,
        match_type=MatchType.REGEX,
        patterns=patterns or [r"bad_\d+_pattern"],
        confidence=0.85,
    )


# ---------------------------------------------------------------------------
# Tests — evaluate()
# ---------------------------------------------------------------------------


class TestEvaluate:
    """Tests for GuardianEngine.evaluate()."""

    def test_safe_input_no_matches(self):
        engine = _make_engine(_keyword_rule())
        matches, latency = engine.evaluate("This is a perfectly safe sentence.")
        assert matches == []
        assert latency >= 0

    def test_keyword_match(self):
        engine = _make_engine(_keyword_rule(keywords=["bomb"]))
        matches, _ = engine.evaluate("how to make a bomb")
        assert len(matches) >= 1
        assert matches[0].rule_id == "test-kw"
        assert matches[0].severity == Severity.HIGH

    def test_regex_match(self):
        engine = _make_engine(_regex_rule(patterns=[r"injection\s+attack"]))
        matches, _ = engine.evaluate("performing an injection attack now")
        assert len(matches) >= 1
        assert matches[0].rule_id == "test-rx"

    def test_empty_text_no_matches(self):
        engine = _make_engine(_keyword_rule())
        matches, _ = engine.evaluate("")
        assert matches == []

    def test_multiple_rules(self):
        r1 = _keyword_rule(rule_id="r1", keywords=["alpha"])
        r2 = _keyword_rule(rule_id="r2", keywords=["beta"])
        engine = _make_engine(r1, r2)

        matches, _ = engine.evaluate("alpha and beta together")
        rule_ids = {m.rule_id for m in matches}
        assert "r1" in rule_ids
        assert "r2" in rule_ids


# ---------------------------------------------------------------------------
# Tests — quick_check()
# ---------------------------------------------------------------------------


class TestQuickCheck:
    """Tests for GuardianEngine.quick_check()."""

    def test_blocked_content(self):
        engine = _make_engine(_keyword_rule(keywords=["danger"]))
        blocked, reason, action = engine.quick_check("this is danger")
        assert blocked is True
        assert reason is not None
        assert action == RuleAction.BLOCK

    def test_safe_content(self):
        engine = _make_engine(_keyword_rule(keywords=["danger"]))
        blocked, reason, action = engine.quick_check("nothing wrong here")
        assert blocked is False
        assert reason is None
        assert action is None

    def test_escalate_high_severity_blocks(self):
        rule = _keyword_rule(
            keywords=["escalate_me"],
            severity=Severity.HIGH,
            action=RuleAction.ESCALATE,
        )
        engine = _make_engine(rule)
        blocked, reason, action = engine.quick_check("please escalate_me now")
        assert blocked is True
        assert action == RuleAction.ESCALATE

    def test_log_action_does_not_block(self):
        rule = _keyword_rule(
            keywords=["log_only"],
            severity=Severity.LOW,
            action=RuleAction.LOG,
        )
        engine = _make_engine(rule)
        blocked, _, _ = engine.quick_check("should log_only this")
        assert blocked is False


# ---------------------------------------------------------------------------
# Tests — cache
# ---------------------------------------------------------------------------


class TestCache:
    """Tests for evaluation caching."""

    def test_clear_cache_resets(self):
        engine = _make_engine(_keyword_rule(keywords=["cached"]))
        engine.evaluate("some cached text", use_cache=True)
        stats_before = engine.get_stats()
        assert stats_before["cache_misses"] >= 1

        engine.clear_cache()
        # Re-evaluate → should be a miss again
        engine.evaluate("some cached text", use_cache=True)
        stats_after = engine.get_stats()
        assert stats_after["cache_misses"] >= 2

    def test_cache_hit_on_repeat(self):
        engine = _make_engine(_keyword_rule(keywords=["repeat"]))
        engine.evaluate("repeat this", use_cache=True)
        engine.evaluate("repeat this", use_cache=True)
        stats = engine.get_stats()
        assert stats["cache_hits"] >= 1


# ---------------------------------------------------------------------------
# Tests — singleton
# ---------------------------------------------------------------------------


class TestSingleton:
    """Tests for get_guardian_engine() singleton."""

    def test_singleton_identity(self):
        a = get_guardian_engine()
        b = get_guardian_engine()
        assert a is b


# ---------------------------------------------------------------------------
# Tests — thread safety
# ---------------------------------------------------------------------------


class TestThreadSafety:
    """Test concurrent evaluate() calls don't crash."""

    def test_concurrent_evaluate(self):
        engine = _make_engine(
            _keyword_rule(keywords=["thread"]),
            _regex_rule(patterns=[r"concurrent_\d+"]),
        )
        errors: list[Exception] = []

        def _worker(text: str) -> None:
            try:
                for _ in range(50):
                    engine.evaluate(text)
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=_worker, args=("thread test",)),
            threading.Thread(target=_worker, args=("concurrent_42",)),
            threading.Thread(target=_worker, args=("safe text",)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert errors == [], f"Concurrent evaluation errors: {errors}"
