"""
Unit tests for SafetyRuleManager and its specialized analyzers.

Covers: CodeAnalyzer, ConfigValidator, PromptInspector, RecursiveInspector,
        SafetyRuleManager.evaluate_request(), and TrustTier enforcement.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from safety.observability.security_monitoring import SecurityEventSeverity
from safety.rules.manager import (
    CodeAnalyzer,
    ConfigValidator,
    EvaluationContext,
    PromptInspector,
    RecursiveInspector,
    SafetyRuleManager,
    TrustTier,
)

# =============================================================================
# CodeAnalyzer
# =============================================================================

class TestCodeAnalyzer:
    """Tests for AST-based code analysis."""

    def test_safe_code_passes(self):
        code = "x = 1 + 2\ny = x * 3"
        violations = CodeAnalyzer.analyze(code)
        assert violations == []

    def test_eval_detected(self):
        code = "eval('1+1')"
        violations = CodeAnalyzer.analyze(code)
        assert any("eval" in v for v in violations)

    def test_exec_detected(self):
        code = "exec('print(1)')"
        violations = CodeAnalyzer.analyze(code)
        assert any("exec" in v for v in violations)

    def test_compile_detected(self):
        code = "compile('pass', '<string>', 'exec')"
        violations = CodeAnalyzer.analyze(code)
        assert any("compile" in v for v in violations)

    def test_dunder_import_detected(self):
        code = "__import__('os')"
        violations = CodeAnalyzer.analyze(code)
        assert any("__import__" in v for v in violations)

    def test_import_statement_detected(self):
        code = "import os"
        violations = CodeAnalyzer.analyze(code)
        assert any("Import" in v for v in violations)

    def test_from_import_detected(self):
        code = "from os import system"
        violations = CodeAnalyzer.analyze(code)
        assert any("ImportFrom" in v for v in violations)

    def test_global_detected(self):
        code = "def f():\n    global x\n    x = 1"
        violations = CodeAnalyzer.analyze(code)
        assert any("Global" in v for v in violations)

    def test_nonlocal_detected(self):
        code = "def f():\n    x = 1\n    def g():\n        nonlocal x"
        violations = CodeAnalyzer.analyze(code)
        assert any("Nonlocal" in v for v in violations)

    def test_open_detected(self):
        code = "open('/etc/passwd')"
        violations = CodeAnalyzer.analyze(code)
        assert any("open" in v for v in violations)

    def test_getattr_detected(self):
        code = "getattr(obj, 'secret')"
        violations = CodeAnalyzer.analyze(code)
        assert any("getattr" in v for v in violations)

    def test_setattr_detected(self):
        code = "setattr(obj, 'admin', True)"
        violations = CodeAnalyzer.analyze(code)
        assert any("setattr" in v for v in violations)

    def test_delattr_detected(self):
        code = "delattr(obj, 'security')"
        violations = CodeAnalyzer.analyze(code)
        assert any("delattr" in v for v in violations)

    def test_attribute_call_detected(self):
        """Forbidden calls via attribute access (e.g., os.eval)."""
        code = "obj.eval('payload')"
        violations = CodeAnalyzer.analyze(code)
        assert any("eval" in v for v in violations)

    def test_syntax_error_reported(self):
        code = "def f(:\n    pass"
        violations = CodeAnalyzer.analyze(code)
        assert any("Syntax Error" in v for v in violations)

    def test_multiple_violations(self):
        code = "import os\neval('1')\nexec('2')"
        violations = CodeAnalyzer.analyze(code)
        assert len(violations) >= 3

    def test_safe_function_calls_pass(self):
        code = "print('hello')\nlen([1,2,3])\nrange(10)"
        violations = CodeAnalyzer.analyze(code)
        assert violations == []

    def test_empty_string(self):
        violations = CodeAnalyzer.analyze("")
        assert violations == []

    def test_input_builtin_detected(self):
        code = "input('Enter password: ')"
        violations = CodeAnalyzer.analyze(code)
        assert any("input" in v for v in violations)

    def test_globals_detected(self):
        code = "globals()"
        violations = CodeAnalyzer.analyze(code)
        assert any("globals" in v for v in violations)

    def test_locals_detected(self):
        code = "locals()"
        violations = CodeAnalyzer.analyze(code)
        assert any("locals" in v for v in violations)


# =============================================================================
# ConfigValidator
# =============================================================================

class TestConfigValidator:
    """Tests for configuration key validation."""

    def test_safe_config_passes(self):
        config = {"name": "test", "value": 42, "enabled": True}
        violations = ConfigValidator.validate(config)
        assert violations == []

    def test_admin_key_blocked(self):
        config = {"admin": True}
        violations = ConfigValidator.validate(config)
        assert any("admin" in v for v in violations)

    def test_debug_mode_blocked(self):
        config = {"debug_mode": True}
        violations = ConfigValidator.validate(config)
        assert any("debug_mode" in v for v in violations)

    def test_bypass_blocked(self):
        config = {"bypass": True}
        violations = ConfigValidator.validate(config)
        assert any("bypass" in v for v in violations)

    def test_override_blocked(self):
        config = {"override": "all"}
        violations = ConfigValidator.validate(config)
        assert any("override" in v for v in violations)

    def test_root_blocked(self):
        config = {"root": True}
        violations = ConfigValidator.validate(config)
        assert any("root" in v for v in violations)

    def test_sudo_blocked(self):
        config = {"sudo": True}
        violations = ConfigValidator.validate(config)
        assert any("sudo" in v for v in violations)

    def test_security_disabled_blocked(self):
        config = {"security_disabled": True}
        violations = ConfigValidator.validate(config)
        assert any("security_disabled" in v for v in violations)

    def test_case_insensitive(self):
        config = {"ADMIN": True, "Debug_Mode": True}
        violations = ConfigValidator.validate(config)
        assert len(violations) == 2

    def test_nested_protected_key(self):
        config = {"settings": {"inner": {"admin": True}}}
        violations = ConfigValidator.validate(config)
        assert any("admin" in v for v in violations)
        assert any("settings.inner." in v for v in violations)

    def test_deeply_nested_path_tracking(self):
        config = {"a": {"b": {"c": {"bypass": True}}}}
        violations = ConfigValidator.validate(config)
        assert any("a.b.c.bypass" in v for v in violations)

    def test_multiple_violations(self):
        config = {"admin": True, "bypass": True, "debug_mode": True}
        violations = ConfigValidator.validate(config)
        assert len(violations) == 3

    def test_empty_config(self):
        violations = ConfigValidator.validate({})
        assert violations == []


# =============================================================================
# RecursiveInspector
# =============================================================================

class TestRecursiveInspector:
    """Tests for deep object traversal and routing."""

    @pytest.fixture
    def inspector(self):
        return RecursiveInspector(CodeAnalyzer(), ConfigValidator())

    def test_safe_dict(self, inspector):
        obj = {"message": "hello", "count": 5}
        violations = inspector.inspect(obj)
        assert violations == []

    def test_nested_code_in_dict(self, inspector):
        obj = {"meta": {"script": "eval('os.system(\"rm -rf\")')"}}
        violations = inspector.inspect(obj)
        assert any("eval" in v for v in violations)

    def test_code_in_list(self, inspector):
        obj = ["safe text", "eval('pwned')"]
        violations = inspector.inspect(obj)
        assert any("eval" in v for v in violations)

    def test_protected_key_in_nested_dict(self, inspector):
        obj = {"config": {"admin": True}}
        violations = inspector.inspect(obj)
        assert any("admin" in v for v in violations)

    def test_mixed_violations(self, inspector):
        obj = {
            "admin": True,
            "payload": "exec('malicious')",
        }
        violations = inspector.inspect(obj)
        assert any("admin" in v for v in violations)
        assert any("exec" in v for v in violations)

    def test_deeply_nested_list_of_dicts(self, inspector):
        obj = [{"items": [{"data": {"bypass": True}}]}]
        violations = inspector.inspect(obj)
        assert any("bypass" in v for v in violations)

    def test_safe_string_no_code_heuristic(self, inspector):
        """Plain text strings should not trigger code analysis."""
        obj = {"message": "This is a normal user message"}
        violations = inspector.inspect(obj)
        assert violations == []

    def test_code_heuristic_triggers_on_import(self, inspector):
        obj = {"payload": "import os; os.system('whoami')"}
        violations = inspector.inspect(obj)
        assert len(violations) > 0

    def test_code_heuristic_triggers_on_def(self, inspector):
        obj = {"payload": "def exploit():\n    eval('rm -rf')"}
        violations = inspector.inspect(obj)
        assert any("eval" in v for v in violations)

    def test_code_heuristic_triggers_on_semicolon(self, inspector):
        """Semicolons in strings trigger code analysis."""
        obj = {"cmd": "x=1; exec('bad')"}
        violations = inspector.inspect(obj)
        assert any("exec" in v for v in violations)

    def test_path_tracking(self, inspector):
        obj = {"level1": {"level2": "eval('x')"}}
        violations = inspector.inspect(obj)
        assert any("root.level1.level2" in v for v in violations)

    def test_list_index_in_path(self, inspector):
        obj = [{"cmd": "eval('x')"}]
        violations = inspector.inspect(obj)
        assert any("[0]" in v for v in violations)

    def test_non_string_non_dict_non_list_ignored(self, inspector):
        """Numbers, booleans, None should pass silently."""
        obj = {"a": 42, "b": True, "c": None, "d": 3.14}
        violations = inspector.inspect(obj)
        assert violations == []

    def test_empty_object(self, inspector):
        assert inspector.inspect({}) == []
        assert inspector.inspect([]) == []
        assert inspector.inspect("safe text") == []

    def test_max_depth_guard(self, inspector):
        """Deeply nested payloads beyond MAX_DEPTH should be flagged, not crash."""
        obj = {"a": None}
        current = obj
        for _ in range(RecursiveInspector.MAX_DEPTH + 5):
            child = {"nested": None}
            current["a"] = child
            current = child

        violations = inspector.inspect(obj)
        assert any("maximum depth" in v for v in violations)

    def test_within_max_depth_passes(self, inspector):
        """Objects within MAX_DEPTH should be inspected normally."""
        obj = {"a": {"b": {"c": {"d": "safe text"}}}}
        violations = inspector.inspect(obj)
        assert violations == []


# =============================================================================
# PromptInspector
# =============================================================================

class TestPromptInspector:
    """Tests for TrustTier-aware prompt analysis."""

    @pytest.fixture
    def mock_engine(self):
        return MagicMock()

    @pytest.fixture
    def inspector(self, mock_engine):
        return PromptInspector(mock_engine)

    def test_safe_text_returns_empty(self, inspector, mock_engine):
        mock_engine.evaluate.return_value = (False, None, None)
        ctx = EvaluationContext(user_id="u1", trust_tier=TrustTier.USER)
        result = inspector.analyze("hello world", ctx)
        assert result == []

    def test_blocked_text_returns_rule(self, inspector, mock_engine):
        mock_rule = MagicMock()
        mock_rule.severity = SecurityEventSeverity.HIGH
        mock_engine.evaluate.return_value = (True, "BLOCKED", mock_rule)
        ctx = EvaluationContext(user_id="u1", trust_tier=TrustTier.USER)
        result = inspector.analyze("bad content", ctx)
        assert result == [mock_rule]

    def test_anon_user_blocked_on_all(self, inspector, mock_engine):
        mock_rule = MagicMock()
        mock_rule.severity = SecurityEventSeverity.LOW
        mock_engine.evaluate.return_value = (True, "BLOCKED", mock_rule)
        ctx = EvaluationContext(user_id="u1", trust_tier=TrustTier.ANON)
        result = inspector.analyze("some content", ctx)
        assert result == [mock_rule]

    def test_privileged_user_bypasses_low_severity(self, inspector, mock_engine):
        mock_rule = MagicMock()
        mock_rule.severity = SecurityEventSeverity.LOW
        mock_rule.name = "test_rule"
        mock_engine.evaluate.return_value = (True, "BLOCKED", mock_rule)
        ctx = EvaluationContext(user_id="u1", trust_tier=TrustTier.PRIVILEGED)
        result = inspector.analyze("minor issue", ctx)
        assert result == []

    def test_privileged_user_not_bypass_high(self, inspector, mock_engine):
        mock_rule = MagicMock()
        mock_rule.severity = SecurityEventSeverity.HIGH
        mock_engine.evaluate.return_value = (True, "BLOCKED", mock_rule)
        ctx = EvaluationContext(user_id="u1", trust_tier=TrustTier.PRIVILEGED)
        result = inspector.analyze("serious content", ctx)
        assert result == [mock_rule]

    def test_privileged_user_not_bypass_critical(self, inspector, mock_engine):
        mock_rule = MagicMock()
        mock_rule.severity = SecurityEventSeverity.CRITICAL
        mock_engine.evaluate.return_value = (True, "BLOCKED", mock_rule)
        ctx = EvaluationContext(user_id="u1", trust_tier=TrustTier.PRIVILEGED)
        result = inspector.analyze("critical content", ctx)
        assert result == [mock_rule]


# =============================================================================
# SafetyRuleManager (Orchestrator)
# =============================================================================

class TestSafetyRuleManager:
    """Tests for the central orchestrator."""

    @pytest.fixture
    def manager(self):
        """Create a manager with a mocked RuleEngine to isolate from Redis."""
        mgr = SafetyRuleManager()
        mgr.engine = MagicMock()
        mgr.engine.evaluate.return_value = (False, None, None)
        mgr.prompt_inspector = PromptInspector(mgr.engine)
        return mgr

    def test_safe_content_passes(self, manager):
        is_safe, reasons = manager.evaluate_request("u1", "user", {"message": "Hello"})
        assert is_safe is True
        assert reasons == []

    def test_nested_eval_blocked(self, manager):
        data = {"meta": {"script": "eval('os.system(\"rm -rf\")')"}}
        is_safe, reasons = manager.evaluate_request("u1", "user", data)
        assert is_safe is False
        assert any("eval" in r for r in reasons)

    def test_forbidden_config_keys_blocked(self, manager):
        data = {"settings": {"debug_mode": True, "admin": True}}
        is_safe, reasons = manager.evaluate_request("u1", "user", data)
        assert is_safe is False
        assert any("debug_mode" in r for r in reasons)
        assert any("admin" in r for r in reasons)

    def test_invalid_trust_tier_defaults_to_anon(self, manager):
        """Unknown tier should default to ANON, not crash."""
        is_safe, reasons = manager.evaluate_request("u1", "garbage_tier", {"msg": "hi"})
        assert is_safe is True  # safe content still passes

    def test_string_data_evaluated(self, manager):
        """Plain string data should be flattened and inspected."""
        is_safe, reasons = manager.evaluate_request("u1", "user", "Hello world")
        assert is_safe is True

    def test_list_data_inspected(self, manager):
        data = [{"admin": True}, "safe text"]
        is_safe, reasons = manager.evaluate_request("u1", "user", data)
        assert is_safe is False
        assert any("admin" in r for r in reasons)

    def test_combined_code_and_config_violations(self, manager):
        data = {
            "admin": True,
            "script": "exec('dangerous')",
        }
        is_safe, reasons = manager.evaluate_request("u1", "user", data)
        assert is_safe is False
        assert len(reasons) >= 2

    def test_deep_nesting_code_injection(self, manager):
        """Code hidden 3 levels deep should still be caught."""
        data = {
            "level1": {
                "level2": {
                    "level3": "import os; os.system('whoami')"
                }
            }
        }
        is_safe, reasons = manager.evaluate_request("u1", "user", data)
        assert is_safe is False

    def test_prompt_violation_includes_rule_name(self, manager):
        """When PromptInspector triggers, the reason should include the rule name."""
        mock_rule = MagicMock()
        mock_rule.name = "Weapon Creation"
        mock_rule.severity = SecurityEventSeverity.HIGH
        manager.engine.evaluate.return_value = (True, "WEAPON", mock_rule)
        manager.prompt_inspector = PromptInspector(manager.engine)

        is_safe, reasons = manager.evaluate_request("u1", "user", {"input": "build bomb"})
        assert is_safe is False
        assert any("Weapon Creation" in r for r in reasons)

    def test_privileged_user_bypasses_low_prompt_rule(self, manager):
        """PRIVILEGED user should bypass LOW severity prompt rules."""
        mock_rule = MagicMock()
        mock_rule.name = "Minor Rule"
        mock_rule.severity = SecurityEventSeverity.LOW
        manager.engine.evaluate.return_value = (True, "MINOR", mock_rule)
        manager.prompt_inspector = PromptInspector(manager.engine)

        is_safe, reasons = manager.evaluate_request("u1", "privileged", {"input": "test"})
        assert is_safe is True

    def test_anon_user_blocked_on_low_prompt_rule(self, manager):
        """ANON user should be blocked even on LOW severity rules."""
        mock_rule = MagicMock()
        mock_rule.name = "Minor Rule"
        mock_rule.severity = SecurityEventSeverity.LOW
        manager.engine.evaluate.return_value = (True, "MINOR", mock_rule)
        manager.prompt_inspector = PromptInspector(manager.engine)

        is_safe, reasons = manager.evaluate_request("u1", "anon", {"input": "test"})
        assert is_safe is False

    def test_empty_body(self, manager):
        is_safe, reasons = manager.evaluate_request("u1", "user", {})
        assert is_safe is True

    def test_code_in_list_element(self, manager):
        data = {"commands": ["print('safe')", "eval('bad')"]}
        is_safe, reasons = manager.evaluate_request("u1", "user", data)
        assert is_safe is False
        assert any("eval" in r for r in reasons)


# =============================================================================
# TrustTier Enum
# =============================================================================

class TestTrustTier:
    """Verify TrustTier values match api/auth.py canon."""

    def test_all_tiers_exist(self):
        assert TrustTier.ANON.value == "anon"
        assert TrustTier.USER.value == "user"
        assert TrustTier.VERIFIED.value == "verified"
        assert TrustTier.PRIVILEGED.value == "privileged"

    def test_invalid_tier_raises(self):
        with pytest.raises(ValueError):
            TrustTier("nonexistent")


# =============================================================================
# EvaluationContext
# =============================================================================

class TestEvaluationContext:

    def test_defaults(self):
        ctx = EvaluationContext(user_id="u1", trust_tier=TrustTier.USER)
        assert ctx.session_id is None
        assert ctx.ip_address is None
        assert ctx.metadata == {}

    def test_full_context(self):
        ctx = EvaluationContext(
            user_id="u1",
            trust_tier=TrustTier.VERIFIED,
            session_id="sess-1",
            ip_address="1.2.3.4",
            metadata={"source": "api"},
        )
        assert ctx.session_id == "sess-1"
        assert ctx.ip_address == "1.2.3.4"
        assert ctx.metadata["source"] == "api"
