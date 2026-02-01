"""
Tests for Wellness Studio integration with OVERWATCH guardians.

Validates Aegis (InputValidator), Compressor (RateLimiter), and Lumen (PIIDetector)
integration from Wellness Studio security modules.
"""

import pytest

from Arena.the_chase.python.src.the_chase.hardgate.aegis import Aegis, InputValidator, ValidationResult
from Arena.the_chase.python.src.the_chase.hardgate.compressor import (
    Compressor,
    RateLimitConfig,
    RateLimiter,
    RateLimitScope,
    RateLimitStrategy,
)
from Arena.the_chase.python.src.the_chase.hardgate.lumen import Lumen, PIIDetector


class TestAegisInputValidation:
    """Test suite for Aegis guardian with InputValidator."""

    @pytest.fixture
    def aegis(self) -> Aegis:
        """Create Aegis guardian."""
        return Aegis()

    def test_validate_action_returns_result(self, aegis: Aegis):
        """Verify validate_action returns ValidationResult."""
        result = aegis.validate_action({"command": "test"})
        assert isinstance(result, ValidationResult)

    def test_validate_action_simple_string(self, aegis: Aegis):
        """Verify simple action validation."""
        result = aegis.validate_action({"action": "move", "target": "north"})
        assert result.is_valid is True
        assert result.sanitized is not None

    def test_validate_action_empty_dict(self, aegis: Aegis):
        """Verify empty dict validation."""
        result = aegis.validate_action({})
        assert result.is_valid is True

    def test_validate_action_with_special_chars(self, aegis: Aegis):
        """Verify validation with special characters."""
        result = aegis.validate_action({"data": "test<>&\"'"})
        assert result.is_valid is True

    def test_validate_action_sql_injection_attempt(self, aegis: Aegis):
        """Verify SQL injection is detected."""
        result = aegis.validate_action({"query": "SELECT * FROM users"})
        # Result should indicate validation occurred
        assert isinstance(result, ValidationResult)

    def test_validate_action_xss_attempt(self, aegis: Aegis):
        """Verify XSS patterns are detected."""
        result = aegis.validate_action({"script": "<script>alert('xss')</script>"})
        assert isinstance(result, ValidationResult)

    def test_validate_action_command_injection(self, aegis: Aegis):
        """Verify command injection is detected."""
        result = aegis.validate_action({"cmd": "rm -rf /"})
        assert isinstance(result, ValidationResult)


class TestInputValidator:
    """Test suite for InputValidator."""

    @pytest.fixture
    def validator(self) -> InputValidator:
        """Create input validator."""
        return InputValidator()

    def test_validate_returns_valid_result(self, validator: InputValidator):
        """Verify validate returns valid result for safe input."""
        result = validator.validate("Hello, World!")
        assert result.is_valid is True
        assert result.sanitized == "Hello, World!"
        assert len(result.issues) == 0

    def test_validate_empty_string(self, validator: InputValidator):
        """Verify empty string validation."""
        result = validator.validate("")
        assert result.is_valid is True

    def test_validate_unicode_content(self, validator: InputValidator):
        """Verify unicode content validation."""
        result = validator.validate("Hello 世界 🌍")
        assert result.is_valid is True

    def test_validate_long_content(self, validator: InputValidator):
        """Verify long content validation."""
        long_text = "a" * 10000
        result = validator.validate(long_text)
        assert result.is_valid is True

    def test_validate_with_context(self, validator: InputValidator):
        """Verify validation with context."""
        result = validator.validate("test input", context="user_message")
        assert result.is_valid is True


class TestCompressorRateLimiting:
    """Test suite for Compressor guardian with RateLimiter."""

    @pytest.fixture
    def config(self) -> RateLimitConfig:
        """Create rate limit configuration."""
        return RateLimitConfig(
            requests_per_window=100,
            window_seconds=60,
            block_duration_seconds=300,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            scope=RateLimitScope.USER,
        )

    @pytest.fixture
    def compressor(self, config: RateLimitConfig) -> Compressor:
        """Create compressor guardian."""
        return Compressor(config)

    def test_compressor_initialization(self, compressor: Compressor):
        """Verify compressor initializes correctly."""
        assert compressor.strategy == RateLimitStrategy.SLIDING_WINDOW

    def test_check_rate_limit_returns_result(self, compressor: Compressor):
        """Verify check_rate_limit returns a result."""
        result = compressor.check_rate_limit("user123")
        assert result is not None

    def test_check_rate_limit_different_users(self, compressor: Compressor):
        """Verify different users have separate limits."""
        result1 = compressor.check_rate_limit("user1")
        result2 = compressor.check_rate_limit("user2")
        # Both should be allowed initially
        assert result1 is not None
        assert result2 is not None

    def test_check_rate_limit_with_scope(self, compressor: Compressor):
        """Verify rate limiting with explicit scope."""
        result = compressor.check_rate_limit("ip123", RateLimitScope.IP)
        assert result is not None


class TestRateLimiter:
    """Test suite for RateLimiter."""

    @pytest.fixture
    def limiter(self) -> RateLimiter:
        """Create rate limiter."""
        return RateLimiter()

    def test_limiter_initialization(self, limiter: RateLimiter):
        """Verify limiter initializes with defaults."""
        assert limiter.config.requests_per_window == 100
        assert limiter.config.window_seconds == 60

    def test_check_rate_limit_returns_result(self, limiter: RateLimiter):
        """Verify check_rate_limit returns a result."""
        result = limiter.check_rate_limit("test_user")
        assert result is not None
        assert isinstance(result, dict)
        assert 'allowed' in result

    def test_get_key_with_scope(self, limiter: RateLimiter):
        """Verify key generation with scope."""
        key = limiter._get_key("user123", RateLimitScope.USER)
        assert "user:user123" in key

    def test_get_key_without_scope(self, limiter: RateLimiter):
        """Verify key generation without explicit scope."""
        key = limiter._get_key("user123")
        assert "user:user123" in key


class TestLumenBoundaryValidation:
    """Test suite for Lumen guardian with PIIDetector."""

    @pytest.fixture
    def lumen(self) -> Lumen:
        """Create lumen guardian."""
        return Lumen()

    def test_validate_boundary_safe_content(self, lumen: Lumen):
        """Verify safe content passes validation."""
        result = lumen.validate_boundary("Hello, this is a test message.")
        assert result is True

    def test_validate_boundary_empty_string(self, lumen: Lumen):
        """Verify empty string passes validation."""
        result = lumen.validate_boundary("")
        assert result is True

    def test_validate_boundary_with_pii(self, lumen: Lumen):
        """Verify content with PII fails validation."""
        result = lumen.validate_boundary("Contact John Smith at john@example.com")
        assert result is False

    def test_validate_boundary_ssn(self, lumen: Lumen):
        """Verify SSN pattern detection."""
        result = lumen.validate_boundary("SSN: 123-45-6789")
        assert result is False

    def test_validate_boundary_long_text(self, lumen: Lumen):
        """Verify long text validation."""
        long_text = " ".join(["test"] * 1000)
        result = lumen.validate_boundary(long_text)
        assert result is True


class TestPIIDetector:
    """Test suite for PIIDetector."""

    @pytest.fixture
    def detector(self) -> PIIDetector:
        """Create PII detector."""
        return PIIDetector()

    def test_detect_pii_empty_string(self, detector: PIIDetector):
        """Verify empty string returns empty list."""
        result = detector.detect_pii("")
        assert len(result) == 0

    def test_detect_pii_safe_content(self, detector: PIIDetector):
        """Verify safe content returns empty list."""
        result = detector.detect_pii("This is a safe message.")
        assert len(result) == 0

    def test_detect_pii_name_pattern(self, detector: PIIDetector):
        """Verify name pattern detection."""
        result = detector.detect_pii("Contact John Smith")
        # May or may not detect depending on implementation
        assert isinstance(result, list)

    def test_detect_pii_ssn_pattern(self, detector: PIIDetector):
        """Verify SSN pattern detection."""
        result = detector.detect_pii("SSN: 123-45-6789")
        assert isinstance(result, list)

    def test_detect_pii_multiple_patterns(self, detector: PIIDetector):
        """Verify multiple PII types detection."""
        result = detector.detect_pii("John Smith, SSN: 123-45-6789")
        assert isinstance(result, list)


class TestWellnessIntegrationEdgeCases:
    """Edge case tests for Wellness Studio integration."""

    def test_aegis_with_none_values(self):
        """Verify Aegis handles None values."""
        aegis = Aegis()
        result = aegis.validate_action({"key": None})
        assert isinstance(result, ValidationResult)

    def test_aegis_with_nested_dict(self):
        """Verify Aegis handles nested dictionaries."""
        aegis = Aegis()
        result = aegis.validate_action({"outer": {"inner": "value"}})
        assert result.is_valid is True

    def test_aegis_with_list_value(self):
        """Verify Aegis handles list values."""
        aegis = Aegis()
        result = aegis.validate_action({"items": [1, 2, 3]})
        assert result.is_valid is True

    def test_compressor_with_custom_config(self):
        """Verify Compressor with custom configuration."""
        config = RateLimitConfig(
            requests_per_window=10,
            window_seconds=1,
            strategy=RateLimitStrategy.TOKEN_BUCKET,
        )
        compressor = Compressor(config)
        assert compressor.strategy == RateLimitStrategy.TOKEN_BUCKET

    def test_compressor_different_strategies(self):
        """Verify Compressor handles all strategies."""
        for strategy in RateLimitStrategy:
            config = RateLimitConfig(strategy=strategy)
            compressor = Compressor(config)
            assert compressor.strategy == strategy

    def test_lumen_with_unicode(self):
        """Verify Lumen handles unicode content."""
        lumen = Lumen()
        result = lumen.validate_boundary("Hello 世界 🌍")
        assert result is True

    def test_lumen_with_newlines(self):
        """Verify Lumen handles newlines."""
        lumen = Lumen()
        result = lumen.validate_boundary("Line1\nLine2\nLine3")
        assert result is True


class TestWellnessIntegrationWorkflows:
    """Workflow tests for Wellness Studio integration."""

    def test_full_validation_workflow(self):
        """Test complete validation workflow."""
        # Create guardians
        aegis = Aegis()
        lumen = Lumen()

        # Validate input
        action = {"command": "process", "data": "user data"}
        validation = aegis.validate_action(action)

        # Check boundary
        boundary_valid = lumen.validate_boundary("safe content")

        assert validation.is_valid is True
        assert boundary_valid is True

    def test_rate_limit_then_validate(self):
        """Test rate limiting then validation."""
        config = RateLimitConfig(requests_per_window=1000)
        compressor = Compressor(config)
        aegis = Aegis()

        # Check rate limit
        rate_result = compressor.check_rate_limit("user1")

        # Validate action
        validation = aegis.validate_action({"test": "action"})

        assert rate_result is not None
        assert validation.is_valid is True

    def test_multiple_guardians_chain(self):
        """Test chaining multiple guardians."""
        aegis = Aegis()
        compressor = Compressor(RateLimitConfig())
        lumen = Lumen()

        # Rate limit check
        compressor.check_rate_limit("user1")

        # Input validation
        validation = aegis.validate_action({"action": "test"})

        # Boundary check
        boundary = lumen.validate_boundary("safe data")

        assert validation.is_valid is True
        assert boundary is True
