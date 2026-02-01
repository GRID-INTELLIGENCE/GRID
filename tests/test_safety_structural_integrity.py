"""
Safety Architecture Structural Integrity Tests.

Tests border crossings, gradient consistency, and stability of the
Grid safety system. Validates that all safety modules integrate correctly.
"""

import pytest


class TestBorder1ConfigToInput:
    """Tests for Configuration → Input boundary (Gradient: 0.0 → 0.3)."""

    def test_safety_config_loads_from_env(self):
        """SafetyConfig should load from environment variables."""
        from grid.safety.config import SafetyConfig

        config = SafetyConfig.from_env()
        assert config is not None
        assert isinstance(config.denylist, list)
        assert isinstance(config.contribution_threshold, float)
        assert 0.0 <= config.contribution_threshold <= 1.0

    def test_sanitization_config_defaults(self):
        """SanitizationConfig should have sensible defaults."""
        from grid.security.input_sanitizer import SanitizationConfig

        config = SanitizationConfig()
        assert config.max_text_length == 100000
        assert config.max_json_depth == 10
        assert config.max_dict_keys == 100
        assert config.max_list_items == 1000

    def test_threat_detector_config_defaults(self):
        """ThreatDetectorConfig should have sensible defaults."""
        from grid.security.threat_detector import ThreatDetectorConfig

        config = ThreatDetectorConfig()
        assert config.rate_limit_window_seconds == 300
        assert config.rate_limit_max_requests == 100
        assert config.auto_block_threshold == 0.9


class TestBorder2InputToGuardrail:
    """Tests for Input → Guardrail boundary (Gradient: 0.3 → 0.6)."""

    def test_sanitizer_detects_xss(self):
        """InputSanitizer should detect XSS patterns."""
        from grid.security.input_sanitizer import InputSanitizer

        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("<script>alert('xss')</script>")

        assert not result.is_safe or result.severity.value != "none"
        assert len(result.modifications_made) > 0

    def test_sanitizer_detects_sql_injection(self):
        """InputSanitizer should detect SQL injection patterns."""
        from grid.security.input_sanitizer import InputSanitizer

        sanitizer = InputSanitizer()
        threats = sanitizer.detect_threats("' OR '1'='1")

        assert len(threats) > 0
        assert any(t["type"] == "sql_injection" for t in threats)

    def test_threat_detector_analyzes_request(self):
        """ThreatDetector should analyze requests and return results."""
        from grid.security.threat_detector import ThreatDetector

        detector = ThreatDetector()
        result = detector.analyze_request({"query": "SELECT * FROM users"}, client_ip="127.0.0.1")

        assert result is not None
        assert hasattr(result, "risk_score")
        assert hasattr(result, "action")
        assert 0.0 <= result.risk_score <= 1.0

    def test_guardrail_validates_command(self):
        """SafetyGuardrails should validate commands."""
        from grid.safety.guardrails import SafetyGuardrails

        # Should not raise for valid command
        SafetyGuardrails.validate_command("analyze")

        # Should work with None
        SafetyGuardrails.validate_command(None)


class TestBorder3GuardrailToTracing:
    """Tests for Guardrail → Tracing boundary (Gradient: 0.6 → 0.8)."""

    def test_trace_context_creation(self):
        """TraceContext should be created with proper defaults."""
        from grid.tracing.action_trace import TraceContext, TraceOrigin

        context = TraceContext(
            origin=TraceOrigin.USER_INPUT, source_module="test_module", source_function="test_function"
        )

        assert context.trace_id is not None
        assert context.origin == TraceOrigin.USER_INPUT
        assert context.parent_trace_id is None

    def test_action_trace_creation(self):
        """ActionTrace should be created with safety fields."""
        from grid.tracing.action_trace import ActionTrace, TraceContext, TraceOrigin

        context = TraceContext(origin=TraceOrigin.SAFETY_ANALYSIS, source_module="test", source_function="test")

        trace = ActionTrace(
            trace_id=context.trace_id, action_type="safety_check", action_name="Test Safety Check", context=context
        )

        assert trace.safety_score is None  # Not set yet
        assert trace.risk_level is None
        assert trace.guardrail_violations == []
        assert trace.compliance_flags == []

    def test_trace_manager_context_manager(self):
        """TraceManager should work as context manager."""
        from grid.tracing.action_trace import TraceOrigin
        from grid.tracing.trace_manager import get_trace_manager

        manager = get_trace_manager()

        with manager.trace_action(
            action_type="test", action_name="Test Action", origin=TraceOrigin.INTERNAL_PIPELINE
        ) as trace:
            trace.safety_score = 0.95
            trace.risk_level = "low"

        assert trace.success is True
        assert trace.safety_score == 0.95


class TestBorder4TracingToAPISafety:
    """Tests for Tracing → API Safety boundary (Gradient: 0.8 → 1.0)."""

    def test_ai_safety_config_creation(self):
        """AISafetyConfig should be created with environment."""
        from application.mothership.security.ai_safety import AISafetyConfig

        config = AISafetyConfig(environment="development")
        assert config.environment == "development"

    def test_api_key_format_validation(self):
        """AISafetyConfig should validate API key formats."""
        from application.mothership.security.ai_safety import AISafetyConfig

        config = AISafetyConfig()

        # Invalid key (too short)
        assert config.validate_api_key_format("short", "openai") is False

        # Valid OpenAI format
        assert config.validate_api_key_format("sk-" + "x" * 48, "openai") is True

    def test_error_message_sanitization(self):
        """AISafetyConfig should sanitize error messages."""
        from application.mothership.security.ai_safety import AISafetyConfig

        config = AISafetyConfig()
        error = Exception("Invalid api_key: sk-secret123")

        sanitized = config.sanitize_error_message(error, "openai")
        assert "sk-secret" not in sanitized


class TestGradientConsistency:
    """Tests for gradient consistency across borders."""

    def test_severity_gradient_ordering(self):
        """ThreatSeverity should have correct gradient ordering."""
        from grid.security.input_sanitizer import ThreatSeverity

        severities = list(ThreatSeverity)
        assert severities[0] == ThreatSeverity.NONE
        assert severities[-1] == ThreatSeverity.CRITICAL

    def test_risk_level_gradient_ordering(self):
        """RiskLevel should have correct gradient ordering."""
        from grid.security.threat_detector import RiskLevel

        levels = list(RiskLevel)
        assert levels[0] == RiskLevel.NONE
        assert levels[-1] == RiskLevel.CRITICAL

    def test_risk_score_to_level_mapping(self):
        """Risk scores should map to correct levels."""
        from grid.security.threat_detector import ThreatDetector

        detector = ThreatDetector()

        # Test gradient boundaries
        assert detector._get_risk_level(0.0).value == "none"
        assert detector._get_risk_level(0.19).value == "none"
        assert detector._get_risk_level(0.2).value == "low"
        assert detector._get_risk_level(0.39).value == "low"
        assert detector._get_risk_level(0.4).value == "medium"
        assert detector._get_risk_level(0.59).value == "medium"
        assert detector._get_risk_level(0.6).value == "high"
        assert detector._get_risk_level(0.79).value == "high"
        assert detector._get_risk_level(0.8).value == "critical"
        assert detector._get_risk_level(1.0).value == "critical"


class TestContrastZones:
    """Tests for high contrast zone transitions."""

    def test_input_to_guardrail_contrast(self):
        """Input (passive) to Guardrail (active) should work correctly."""
        from grid.safety.guardrails import SafetyGuardrails
        from grid.security.input_sanitizer import InputSanitizer

        sanitizer = InputSanitizer()

        # Sanitize input
        sanitizer.sanitize_text_full("test input")

        # Feed to guardrails (conceptual - guardrails operate on commands)
        SafetyGuardrails.run_all_checks(command=None)

    def test_guardrail_to_tracing_contrast(self):
        """Guardrail (action) to Tracing (observation) should record properly."""
        from grid.safety.guardrails import GuardrailError, SafetyGuardrails
        from grid.tracing.action_trace import TraceOrigin
        from grid.tracing.trace_manager import get_trace_manager

        manager = get_trace_manager()

        with manager.trace_action(
            action_type="guardrail_check", action_name="Validate Command", origin=TraceOrigin.GUARDRAIL_VIOLATION
        ) as trace:
            try:
                SafetyGuardrails.run_all_checks()
            except GuardrailError as e:
                trace.guardrail_violations.append(str(e))
                trace.success = False


class TestStructuralIntegrity:
    """Tests for structural integrity of safety architecture."""

    def test_all_trace_origins_defined(self):
        """All TraceOrigin values should be accessible."""
        from grid.tracing.action_trace import TraceOrigin

        expected_origins = [
            "USER_INPUT",
            "API_REQUEST",
            "SCHEDULED_TASK",
            "EVENT_TRIGGER",
            "SYSTEM_INIT",
            "COGNITIVE_DECISION",
            "PATTERN_MATCH",
            "EXTERNAL_WEBHOOK",
            "INTERNAL_PIPELINE",
            "EMERGENCY_REALTIME",
            "MODEL_INFERENCE",
            "SAFETY_ANALYSIS",
            "COMPLIANCE_CHECK",
            "GUARDRAIL_VIOLATION",
            "RISK_ASSESSMENT",
            "PROMPT_VALIDATION",
            "PII_DETECTION",
        ]

        for origin in expected_origins:
            assert hasattr(TraceOrigin, origin), f"Missing TraceOrigin: {origin}"

    def test_all_threat_types_defined(self):
        """All ThreatType values should be accessible."""
        from grid.security.input_sanitizer import ThreatType

        expected_types = [
            "XSS",
            "SQL_INJECTION",
            "COMMAND_INJECTION",
            "CODE_INJECTION",
            "PATH_TRAVERSAL",
            "OVERSIZED_INPUT",
            "DEEP_NESTING",
            "INVALID_ENCODING",
            "SUSPICIOUS_PATTERN",
        ]

        for threat_type in expected_types:
            assert hasattr(ThreatType, threat_type), f"Missing ThreatType: {threat_type}"

    def test_all_threat_categories_defined(self):
        """All ThreatCategory values should be accessible."""
        from grid.security.threat_detector import ThreatCategory

        expected_categories = [
            "INJECTION",
            "XSS",
            "BRUTE_FORCE",
            "RATE_LIMIT",
            "DOS",
            "ENUMERATION",
            "RECONNAISSANCE",
            "DATA_EXFILTRATION",
            "PRIVILEGE_ESCALATION",
            "MALICIOUS_PAYLOAD",
            "ANOMALY",
        ]

        for category in expected_categories:
            assert hasattr(ThreatCategory, category), f"Missing ThreatCategory: {category}"

    def test_production_security_environments(self):
        """All security environments should be configured."""
        from grid.security.production import Environment, ProductionSecurityManager

        for env in Environment:
            assert env in ProductionSecurityManager.SECURITY_CONFIGS


class TestStability:
    """Tests for system stability under various conditions."""

    def test_sanitizer_handles_empty_input(self):
        """InputSanitizer should handle empty input."""
        from grid.security.input_sanitizer import InputSanitizer

        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text("")
        assert result == ""

    def test_sanitizer_handles_large_input(self):
        """InputSanitizer should handle large input."""
        from grid.security.input_sanitizer import InputSanitizer

        sanitizer = InputSanitizer()
        large_input = "x" * 200000
        result = sanitizer.sanitize_text_full(large_input)

        assert result.sanitized_length <= 100000 + 20  # +20 for truncation message

    def test_sanitizer_handles_nested_json(self):
        """InputSanitizer should handle deeply nested JSON."""
        from grid.security.input_sanitizer import InputSanitizer

        sanitizer = InputSanitizer()

        # Create deeply nested structure
        nested = {"level": 0}
        current = nested
        for i in range(15):
            current["child"] = {"level": i + 1}
            current = current["child"]

        result = sanitizer.sanitize_json_full(nested)
        assert result is not None

    def test_threat_detector_handles_rapid_requests(self):
        """ThreatDetector should handle rapid requests with rate limiting."""
        from grid.security.threat_detector import ThreatDetector

        detector = ThreatDetector()

        # Simulate rapid requests
        for i in range(50):
            result = detector.analyze_request({"query": f"test {i}"}, client_ip="192.168.1.1")
            assert result is not None

    def test_trace_manager_handles_nested_traces(self):
        """TraceManager should handle nested traces correctly."""
        from grid.tracing.action_trace import TraceOrigin
        from grid.tracing.trace_manager import get_trace_manager

        manager = get_trace_manager()

        with manager.trace_action(
            action_type="outer", action_name="Outer Action", origin=TraceOrigin.INTERNAL_PIPELINE
        ) as outer:
            with manager.trace_action(
                action_type="inner", action_name="Inner Action", origin=TraceOrigin.INTERNAL_PIPELINE
            ) as inner:
                assert inner.context.parent_trace_id == outer.trace_id


class TestThresholdEnforcement:
    """Tests for threshold enforcement across environments."""

    def test_development_thresholds(self):
        """Development environment should have permissive thresholds."""
        from grid.security.production import Environment, ProductionSecurityManager

        config = ProductionSecurityManager.SECURITY_CONFIGS[Environment.DEVELOPMENT]
        assert config.min_contribution_score == 0.0
        assert config.check_contribution is False
        assert config.max_failed_attempts == 100

    def test_production_thresholds(self):
        """Production environment should have restrictive thresholds."""
        from grid.security.production import Environment, ProductionSecurityManager

        config = ProductionSecurityManager.SECURITY_CONFIGS[Environment.PRODUCTION]
        assert config.min_contribution_score == 0.8
        assert config.check_contribution is True
        assert config.max_failed_attempts == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
