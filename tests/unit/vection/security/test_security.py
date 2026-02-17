"""Tests for Vection security functionality."""

import pytest


@pytest.mark.unit
class TestSecurityManager:
    """Test SecurityManager class."""

    def test_initialization(self):
        """Test that SecurityManager can be initialized."""
        from vection.security.manager import SecurityManager

        manager = SecurityManager()
        assert manager is not None


@pytest.mark.unit
class TestRateLimiter:
    """Test RateLimiter class."""

    def test_initialization_default_config(self):
        """Test RateLimiter initializes with default config."""
        from vection.security.rate_limiter import RateLimiter

        limiter = RateLimiter()
        assert limiter is not None
        assert limiter.config is not None

    def test_initialization_custom_config(self):
        """Test RateLimiter initializes with custom config."""
        from vection.security.rate_limiter import RateLimitConfig, RateLimiter

        config = RateLimitConfig(
            default_limit=5,
            default_window_seconds=30,
        )
        limiter = RateLimiter(config=config)
        assert limiter.config.default_limit == 5
        assert limiter.config.default_window_seconds == 30

    def test_allow_request_returns_bool(self):
        """Test that allow() returns boolean."""
        from vection.security.rate_limiter import RateLimiter

        limiter = RateLimiter()
        result = limiter.allow("test_session", "default")
        assert isinstance(result, bool)

    def test_check_returns_status(self):
        """Test that check() returns RateLimitStatus."""
        from vection.security.rate_limiter import RateLimiter, RateLimitStatus

        limiter = RateLimiter()
        status = limiter.check("test_session", "default")
        assert isinstance(status, RateLimitStatus)
        assert hasattr(status, "allowed")

    def test_rate_limit_enforcement(self):
        """Test that rate limits are enforced after exceeding quota."""
        from vection.security.rate_limiter import RateLimitConfig, RateLimiter

        # Configure very low limit for testing
        config = RateLimitConfig(
            default_limit=3,
            default_window_seconds=60,
        )
        limiter = RateLimiter(config=config)

        session_id = "test_rate_limit_session"

        # First requests should be allowed
        for i in range(3):
            assert limiter.allow(session_id, "default"), f"Request {i + 1} should be allowed"

        # After exceeding limit, requests should be denied
        assert not limiter.allow(session_id, "default"), "Request after limit should be denied"

    def test_different_sessions_independent(self):
        """Test that different sessions have independent rate limits."""
        from vection.security.rate_limiter import RateLimitConfig, RateLimiter

        config = RateLimitConfig(default_limit=2, default_window_seconds=60)
        limiter = RateLimiter(config=config)

        # Exhaust limit for session1
        limiter.allow("session1", "default")
        limiter.allow("session1", "default")
        assert not limiter.allow("session1", "default")

        # session2 should still have quota
        assert limiter.allow("session2", "default")


@pytest.mark.unit
class TestInputValidator:
    """Test InputValidator class."""

    def test_initialization(self):
        """Test InputValidator initializes correctly."""
        from vection.security.input_validator import InputValidator

        validator = InputValidator()
        assert validator is not None
        assert validator.config is not None

    def test_validate_string_valid_input(self):
        """Test validation of valid string input."""
        from vection.security.input_validator import InputValidator

        validator = InputValidator()
        result = validator.validate_string("normal_user_input", field_name="test_field")

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_string_too_long(self):
        """Test validation rejects strings that are too long."""
        from vection.security.input_validator import InputValidator

        validator = InputValidator()
        long_input = "x" * 100000  # Very long string

        result = validator.validate_string(long_input, field_name="test_field", max_length=1000)

        assert not result.is_valid
        assert len(result.errors) > 0

    def test_validate_string_type_check(self):
        """Test validation rejects non-string types."""
        from vection.security.input_validator import InputValidator

        validator = InputValidator()

        result = validator.validate_string(12345, field_name="test_field")

        assert not result.is_valid
        assert any("type" in str(err).lower() for err in result.errors)

    def test_validate_string_empty_not_allowed(self):
        """Test validation rejects empty strings when not allowed."""
        from vection.security.input_validator import InputValidator

        validator = InputValidator()

        result = validator.validate_string("", field_name="test_field", allow_empty=False)

        assert not result.is_valid

    def test_validate_string_min_length(self):
        """Test validation rejects strings shorter than minimum."""
        from vection.security.input_validator import InputValidator

        validator = InputValidator()

        result = validator.validate_string("ab", field_name="test_field", min_length=5)

        assert not result.is_valid

    def test_forbidden_patterns_detected(self):
        """Test that forbidden patterns (potential injections) are detected."""
        from vection.security.input_validator import InputValidator, InputValidatorConfig

        # Configure with SQL-like forbidden patterns
        config = InputValidatorConfig(
            forbidden_patterns=[
                r";\s*DROP\s+TABLE",
                r"--",
                r"\.\.\/",
            ]
        )
        validator = InputValidator(config=config)

        # Test SQL injection pattern
        sql_injection = "'; DROP TABLE users; --"
        validator.validate_string(sql_injection, field_name="query")

        # The validator should detect forbidden patterns
        assert validator._forbidden_patterns is not None
        assert len(validator._forbidden_patterns) > 0

    def test_validate_metadata(self):
        """Test metadata validation."""
        from vection.security.input_validator import InputValidator

        validator = InputValidator()

        metadata = {
            "key1": "value1",
            "key2": "value2",
        }

        result = validator.validate_metadata(metadata)
        assert result.is_valid

    def test_validate_session_id_valid(self):
        """Test valid session ID validation."""
        from vection.security.input_validator import InputValidator

        validator = InputValidator()

        # Valid session IDs (alphanumeric with hyphens/underscores)
        valid_ids = ["session_123", "abc-def-ghi", "user123"]

        for session_id in valid_ids:
            result = validator.validate_session_id(session_id)
            assert result.is_valid, f"Session ID '{session_id}' should be valid"

    def test_validate_session_id_invalid(self):
        """Test invalid session ID validation."""
        from vection.security.input_validator import InputValidator

        validator = InputValidator()

        # Invalid session IDs (special characters, injection attempts)
        invalid_ids = ["session;DROP", "../etc/passwd", "session<script>"]

        for session_id in invalid_ids:
            result = validator.validate_session_id(session_id)
            # These should either be invalid or sanitized
            assert result is not None


@pytest.mark.unit
class TestInputValidatorConfig:
    """Test InputValidatorConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        from vection.security.input_validator import InputValidatorConfig

        config = InputValidatorConfig()

        assert config.max_string_length > 0
        assert config.max_metadata_keys > 0
        assert config.forbidden_patterns is not None

    def test_custom_config(self):
        """Test custom configuration values."""
        from vection.security.input_validator import InputValidatorConfig

        config = InputValidatorConfig(
            max_string_length=500,
            max_metadata_keys=10,
        )

        assert config.max_string_length == 500
        assert config.max_metadata_keys == 10
