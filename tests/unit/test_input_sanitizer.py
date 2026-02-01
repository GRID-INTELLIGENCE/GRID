"""
Unit tests for GRID Input Sanitizer module.

Tests cover:
- XSS detection and removal
- SQL injection blocking
- Command injection prevention
- Path traversal protection
- Code injection detection
- Unicode normalization
- Length limits and truncation
- JSON structure validation
- Threat severity assessment
"""

from __future__ import annotations

from grid.security.input_sanitizer import (
    InputSanitizer,
    SanitizationConfig,
    ThreatSeverity,
    ThreatType,
    get_sanitizer,
    is_safe,
    sanitize_json,
    sanitize_text,
)


class TestXSSDetection:
    """Tests for XSS threat detection."""

    def test_script_tag_detection(self):
        """Should detect and remove script tags."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full('<script>alert("xss")</script>')

        assert result.is_safe is False
        assert "<script>" not in str(result.sanitized_content)
        assert any(t["type"] == ThreatType.XSS.value for t in result.threats_detected)

    def test_javascript_protocol(self):
        """Should detect javascript: protocol."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("javascript:alert(1)")

        assert result.is_safe is False
        assert "javascript:" not in str(result.sanitized_content)

    def test_on_event_handler(self):
        """Should detect on* event handlers."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("<img src=x onerror=alert(1)>")

        assert result.is_safe is False

    def test_safe_html_entities(self):
        """Should encode HTML entities."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("<div>safe content</div>")

        sanitized = str(result.sanitized_content)
        assert "&lt;" in sanitized
        assert "&gt;" in sanitized


class TestSQLInjectionDetection:
    """Tests for SQL injection detection."""

    def test_union_select_detection(self):
        """Should detect UNION SELECT attacks."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("' OR '1'='1' UNION SELECT * FROM users")

        assert result.is_safe is False
        assert any(t["type"] == ThreatType.SQL_INJECTION.value for t in result.threats_detected)

    def test_drop_table_detection(self):
        """Should detect DROP TABLE attacks."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("'; DROP TABLE users; --")

        assert result.is_safe is False

    def test_insert_into_detection(self):
        """Should detect INSERT INTO attacks."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("'); INSERT INTO users VALUES ('hacker'); --")

        assert result.is_safe is False


class TestCommandInjectionDetection:
    """Tests for command injection detection."""

    def test_pipe_command(self):
        """Should detect pipe command injection."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("file.txt; rm -rf /")

        assert result.is_safe is False

    def test_backtick_execution(self):
        """Should detect backtick command execution."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("`cat /etc/passwd`")

        assert result.is_safe is False

    def test_subprocess_call(self):
        """Should detect subprocess calls."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("subprocess.call(['rm', '-rf', '/'])")

        assert result.is_safe is False


class TestCodeInjectionDetection:
    """Tests for code injection detection."""

    def test_eval_detection(self):
        """Should detect eval() calls."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("eval('malicious code')")

        assert result.is_safe is False

    def test_exec_detection(self):
        """Should detect exec() calls."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("exec('malicious')")

        assert result.is_safe is False

    def test_os_system_detection(self):
        """Should detect os.system() calls."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("os.system('rm -rf /')")

        assert result.is_safe is False


class TestPathTraversalDetection:
    """Tests for path traversal detection."""

    def test_double_slash_detection(self):
        """Should detect ../ path traversal."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("../../../etc/passwd")

        assert result.is_safe is False

    def test_encoded_path_traversal(self):
        """Should detect URL-encoded path traversal."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("%2e%2e%2fetc%2fpasswd")

        assert result.is_safe is False

    def test_windows_path_traversal(self):
        """Should detect Windows path traversal."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("..\\..\\..\\windows\\system32")

        assert result.is_safe is False


class TestLengthLimits:
    """Tests for length limit enforcement."""

    def test_text_truncation(self):
        """Should truncate oversized text."""
        config = SanitizationConfig(max_text_length=100, truncate_oversized=True)
        sanitizer = InputSanitizer(config)
        long_text = "x" * 200

        result = sanitizer.sanitize_text_full(long_text)

        assert len(str(result.sanitized_content)) <= 115  # 100 + "... [truncated]"
        assert "truncated" in result.modifications_made

    def test_json_key_limit(self):
        """Should limit dictionary keys."""
        config = SanitizationConfig(max_dict_keys=5)
        sanitizer = InputSanitizer(config)
        large_dict = {f"key{i}": f"value{i}" for i in range(10)}

        result = sanitizer.sanitize_json_full(large_dict)

        sanitized = result.sanitized_content
        assert len(sanitized) <= 5

    def test_json_list_limit(self):
        """Should limit list items."""
        config = SanitizationConfig(max_list_items=5)
        sanitizer = InputSanitizer(config)
        large_list = list(range(10))

        result = sanitizer.sanitize_json_full({"data": large_list})

        sanitized = result.sanitized_content
        assert len(sanitized["data"]) <= 5


class TestUnicodeNormalization:
    """Tests for Unicode normalization."""

    def test_unicode_normalization(self):
        """Should normalize Unicode characters."""
        config = SanitizationConfig(normalize_unicode=True)
        sanitizer = InputSanitizer(config)

        # Test with combining characters that need normalization
        text = "cafe\u0301"  # cafe with combining accent (e + combining acute)
        result = sanitizer.sanitize_text_full(text)

        # Check if normalization happened (café should be normalized)
        assert "unicode_normalized" in result.modifications_made or result.sanitized_content != text


class TestJSONSanitization:
    """Tests for JSON structure sanitization."""

    def test_nested_json_sanitization(self):
        """Should sanitize nested JSON structures."""
        sanitizer = InputSanitizer()
        data = {
            "safe": "value",
            "dangerous": "<script>alert(1)</script>",
            "nested": {"xss": "javascript:alert(1)", "safe": "ok"},
        }

        result = sanitizer.sanitize_json_full(data)

        sanitized = result.sanitized_content
        assert "<script>" not in str(sanitized.get("dangerous", ""))
        assert "javascript:" not in str(sanitized["nested"].get("xss", ""))

    def test_deep_nesting_protection(self):
        """Should protect against deep nesting."""
        config = SanitizationConfig(max_json_depth=3)
        sanitizer = InputSanitizer(config)

        # Create deeply nested structure
        nested = {"level": 1}
        current = nested
        for i in range(2, 10):
            current["next"] = {"level": i}
            current = current["next"]

        result = sanitizer.sanitize_json_full(nested)

        assert any(t["type"] == ThreatType.DEEP_NESTING.value for t in result.threats_detected)

    def test_list_sanitization(self):
        """Should sanitize items in lists."""
        sanitizer = InputSanitizer()
        data = {"items": ["safe", "<script>alert(1)</script>", "normal"]}

        result = sanitizer.sanitize_json_full(data)

        sanitized = result.sanitized_content
        assert "<script>" not in str(sanitized["items"][1])


class TestThreatSeverity:
    """Tests for threat severity assessment."""

    def test_critical_severity(self):
        """Should detect critical severity threats."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("<script>alert('xss')</script>")

        assert result.severity == ThreatSeverity.CRITICAL

    def test_high_severity(self):
        """Should detect high severity threats."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("javascript:alert(1)")

        assert result.severity in [ThreatSeverity.HIGH, ThreatSeverity.CRITICAL]

    def test_no_threats(self):
        """Should mark safe input with no threats."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("safe text content")

        assert result.is_safe is True
        assert result.severity == ThreatSeverity.NONE

    def test_strict_mode(self):
        """Strict mode should reject any suspicious input."""
        config = SanitizationConfig(strict_mode=True)
        sanitizer = InputSanitizer(config)
        result = sanitizer.sanitize_text_full("text with <br> tag")

        assert result.is_safe is False


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_get_sanitizer_singleton(self):
        """Should return singleton instance."""
        sanitizer1 = get_sanitizer()
        sanitizer2 = get_sanitizer()
        assert sanitizer1 is sanitizer2

    def test_sanitize_text_function(self):
        """Should use default sanitizer."""
        result = sanitize_text("<script>alert(1)</script>")
        assert "<script>" not in result

    def test_sanitize_json_function(self):
        """Should sanitize JSON using default sanitizer."""
        data = {"key": "<script>alert(1)</script>"}
        result = sanitize_json(data)
        assert "<script>" not in str(result.get("key", ""))

    def test_is_safe_function(self):
        """Should check if text is safe."""
        assert is_safe("safe text") is True
        assert is_safe("<script>alert(1)</script>") is False


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_input(self):
        """Should handle empty input."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full("")

        assert result.is_safe is True
        assert result.sanitized_content == ""

    def test_none_input(self):
        """Should handle None input."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full(None)

        assert result.sanitized_content == "None"

    def test_numeric_input(self):
        """Should handle numeric input."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_text_full(12345)

        assert result.sanitized_content == "12345"

    def test_special_characters(self):
        """Should preserve safe special characters."""
        InputSanitizer()
        result = sanitize_text("Hello, World! How are you?")

        assert "Hello, World!" in result
        assert "How are you?" in result

    def test_multiline_input(self):
        """Should handle multiline input."""
        sanitizer = InputSanitizer()
        text = "line1\nline2\nline3"
        result = sanitizer.sanitize_text_full(text)

        assert "line1" in str(result.sanitized_content)
        assert "line2" in str(result.sanitized_content)
        assert "line3" in str(result.sanitized_content)

    def test_unicode_characters(self):
        """Should handle Unicode characters."""
        InputSanitizer()
        result = sanitize_text("Hello 世界 🌍")

        assert "Hello 世界 🌍" in result or "Hello" in result
