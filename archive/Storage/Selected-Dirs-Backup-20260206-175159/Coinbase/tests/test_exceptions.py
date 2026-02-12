"""Comprehensive tests for the exceptions module.

This module tests:
- ErrorCode and ErrorSeverity enums
- ErrorContext dataclass
- All exception classes in the hierarchy
- Utility functions (wrap_exception, is_recoverable)
- Method chaining and serialization
"""

from datetime import datetime

import pytest

from coinbase.exceptions import (
    # Agent
    AgentError,
    APIError,
    AuthenticationError,
    # Auth
    AuthError,
    AuthorizationError,
    CognitiveError,
    # Base
    CoinbaseError,
    # Configuration
    ConfigurationError,
    ConnectionError,
    # Crypto
    CryptoError,
    # Database
    DatabaseError,
    DecryptionError,
    EncryptionError,
    # Enums
    ErrorCode,
    # Context
    ErrorContext,
    ErrorSeverity,
    InitializationError,
    InsufficientFundsError,
    InvalidInputError,
    InvalidSymbolError,
    MissingFieldError,
    # Network
    NetworkError,
    PermissionDeniedError,
    PortfolioError,
    QueryError,
    RateLimitError,
    ResourceAlreadyExistsError,
    # Resource
    ResourceError,
    ResourceNotFoundError,
    # Security
    SecurityError,
    SecurityPolicyViolationError,
    SkillExecutionError,
    SkillNotFoundError,
    TimeoutError,
    TradeError,
    TransactionError,
    # Validation
    ValidationError,
    ValueOutOfRangeError,
    is_recoverable,
    # Utilities
    wrap_exception,
)


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_error_code_values_are_integers(self) -> None:
        """Error codes should be integers."""
        assert isinstance(ErrorCode.UNKNOWN_ERROR.value, int)
        assert isinstance(ErrorCode.VALIDATION_ERROR.value, int)
        assert isinstance(ErrorCode.AUTH_ERROR.value, int)

    def test_error_code_ranges(self) -> None:
        """Error codes should be in correct ranges."""
        # General errors: 1000-1999
        assert 1000 <= ErrorCode.UNKNOWN_ERROR.value < 2000
        assert 1000 <= ErrorCode.INTERNAL_ERROR.value < 2000

        # Validation errors: 2000-2999
        assert 2000 <= ErrorCode.VALIDATION_ERROR.value < 3000
        assert 2000 <= ErrorCode.INVALID_INPUT.value < 3000

        # Auth errors: 3000-3999
        assert 3000 <= ErrorCode.AUTH_ERROR.value < 4000
        assert 3000 <= ErrorCode.AUTHENTICATION_FAILED.value < 4000

        # Resource errors: 4000-4999
        assert 4000 <= ErrorCode.RESOURCE_ERROR.value < 5000
        assert 4000 <= ErrorCode.RESOURCE_NOT_FOUND.value < 5000

        # Network errors: 5000-5999
        assert 5000 <= ErrorCode.NETWORK_ERROR.value < 6000
        assert 5000 <= ErrorCode.RATE_LIMITED.value < 6000

        # Database errors: 6000-6999
        assert 6000 <= ErrorCode.DATABASE_ERROR.value < 7000
        assert 6000 <= ErrorCode.QUERY_FAILED.value < 7000

        # Crypto errors: 7000-7999
        assert 7000 <= ErrorCode.CRYPTO_ERROR.value < 8000
        assert 7000 <= ErrorCode.INSUFFICIENT_FUNDS.value < 8000

        # Security errors: 8000-8999
        assert 8000 <= ErrorCode.SECURITY_ERROR.value < 9000
        assert 8000 <= ErrorCode.ENCRYPTION_FAILED.value < 9000

        # Agent errors: 9000-9999
        assert 9000 <= ErrorCode.AGENT_ERROR.value < 10000
        assert 9000 <= ErrorCode.SKILL_NOT_FOUND.value < 10000

    def test_error_code_uniqueness(self) -> None:
        """All error codes should be unique."""
        values = [code.value for code in ErrorCode]
        assert len(values) == len(set(values))


class TestErrorSeverity:
    """Tests for ErrorSeverity enum."""

    def test_severity_levels_exist(self) -> None:
        """All severity levels should exist."""
        assert ErrorSeverity.DEBUG
        assert ErrorSeverity.INFO
        assert ErrorSeverity.WARNING
        assert ErrorSeverity.ERROR
        assert ErrorSeverity.CRITICAL


class TestErrorContext:
    """Tests for ErrorContext dataclass."""

    def test_default_context(self) -> None:
        """ErrorContext should have sensible defaults."""
        context = ErrorContext()
        assert isinstance(context.timestamp, datetime)
        assert context.component is None
        assert context.operation is None
        assert context.user_id is None
        assert context.request_id is None
        assert context.correlation_id is None
        assert context.metadata == {}
        assert context.stack_trace is None

    def test_context_with_values(self) -> None:
        """ErrorContext should accept values."""
        context = ErrorContext(
            component="TestComponent",
            operation="test_operation",
            user_id="user123",
            request_id="req456",
            metadata={"key": "value"},
        )
        assert context.component == "TestComponent"
        assert context.operation == "test_operation"
        assert context.user_id == "user123"
        assert context.request_id == "req456"
        assert context.metadata == {"key": "value"}

    def test_context_to_dict(self) -> None:
        """ErrorContext should convert to dictionary."""
        context = ErrorContext(
            component="TestComponent",
            user_id="user123",
        )
        result = context.to_dict()
        assert isinstance(result, dict)
        assert result["component"] == "TestComponent"
        assert result["user_id"] == "user123"
        assert "timestamp" in result


class TestCoinbaseError:
    """Tests for base CoinbaseError class."""

    def test_basic_error(self) -> None:
        """CoinbaseError should work with just a message."""
        error = CoinbaseError("Something went wrong")
        assert str(error) == "[UNKNOWN_ERROR] Something went wrong"
        assert error.message == "Something went wrong"
        assert error.code == ErrorCode.UNKNOWN_ERROR
        assert error.severity == ErrorSeverity.ERROR
        assert error.recoverable is False

    def test_error_with_code(self) -> None:
        """CoinbaseError should accept error code."""
        error = CoinbaseError("Test error", code=ErrorCode.INTERNAL_ERROR)
        assert error.code == ErrorCode.INTERNAL_ERROR

    def test_error_with_severity(self) -> None:
        """CoinbaseError should accept severity."""
        error = CoinbaseError("Warning", severity=ErrorSeverity.WARNING)
        assert error.severity == ErrorSeverity.WARNING

    def test_error_recoverable(self) -> None:
        """CoinbaseError should track recoverability."""
        error = CoinbaseError("Retryable error", recoverable=True)
        assert error.recoverable is True

    def test_error_with_cause(self) -> None:
        """CoinbaseError should chain exceptions."""
        original = ValueError("Original error")
        error = CoinbaseError("Wrapped error", cause=original)
        assert error.cause is original
        assert error.__cause__ is original

    def test_with_context_method(self) -> None:
        """with_context should add context info."""
        error = CoinbaseError("Test error")
        result = error.with_context(
            component="TestComponent",
            operation="test_op",
            custom_field="custom_value",
        )
        assert result is error  # Returns self for chaining
        assert error.context.component == "TestComponent"
        assert error.context.operation == "test_op"
        assert error.context.metadata["custom_field"] == "custom_value"

    def test_to_dict(self) -> None:
        """to_dict should return serializable dictionary."""
        error = CoinbaseError(
            "Test error",
            code=ErrorCode.INTERNAL_ERROR,
            severity=ErrorSeverity.ERROR,
            recoverable=True,
        )
        result = error.to_dict()
        assert result["error"] is True
        assert result["code"] == ErrorCode.INTERNAL_ERROR.value
        assert result["code_name"] == "INTERNAL_ERROR"
        assert result["message"] == "Test error"
        assert result["severity"] == "ERROR"
        assert result["recoverable"] is True
        assert "context" in result

    def test_repr(self) -> None:
        """__repr__ should be informative."""
        error = CoinbaseError("Test", code=ErrorCode.INTERNAL_ERROR)
        repr_str = repr(error)
        assert "CoinbaseError" in repr_str
        assert "INTERNAL_ERROR" in repr_str


class TestValidationErrors:
    """Tests for validation error classes."""

    def test_validation_error(self) -> None:
        """ValidationError should track field and value."""
        error = ValidationError("Invalid data", field="email", value="bad")
        assert error.field == "email"
        assert error.value == "bad"
        assert error.context.metadata["field"] == "email"

    def test_invalid_input_error(self) -> None:
        """InvalidInputError should have correct code."""
        error = InvalidInputError("Bad input", field="name", value=123)
        assert error.code == ErrorCode.INVALID_INPUT
        assert error.field == "name"

    def test_missing_field_error(self) -> None:
        """MissingFieldError should format message correctly."""
        error = MissingFieldError("username")
        assert "username" in str(error)
        assert error.code == ErrorCode.MISSING_REQUIRED_FIELD
        assert error.field == "username"

    def test_value_out_of_range_error(self) -> None:
        """ValueOutOfRangeError should include range info."""
        error = ValueOutOfRangeError("age", value=-5, min_value=0, max_value=150)
        assert error.min_value == 0
        assert error.max_value == 150
        assert "-5" in str(error)
        assert "min=0" in str(error)
        assert "max=150" in str(error)


class TestAuthErrors:
    """Tests for authentication/authorization errors."""

    def test_auth_errors_not_recoverable(self) -> None:
        """Auth errors should not be recoverable."""
        errors = [
            AuthError("Auth failed"),
            AuthenticationError(),
            AuthorizationError(),
            PermissionDeniedError("delete", "resource"),
        ]
        for error in errors:
            assert error.recoverable is False

    def test_authentication_error(self) -> None:
        """AuthenticationError should have default message."""
        error = AuthenticationError()
        assert "Authentication failed" in str(error)
        assert error.code == ErrorCode.AUTHENTICATION_FAILED

    def test_authorization_error_with_resource(self) -> None:
        """AuthorizationError should track resource."""
        error = AuthorizationError("Not authorized", resource="/api/admin")
        assert error.resource == "/api/admin"
        assert error.context.metadata["resource"] == "/api/admin"

    def test_permission_denied_error(self) -> None:
        """PermissionDeniedError should track operation and resource."""
        error = PermissionDeniedError("delete", resource="user/123")
        assert error.operation == "delete"
        assert error.resource == "user/123"
        assert "delete" in str(error)


class TestResourceErrors:
    """Tests for resource errors."""

    def test_resource_not_found(self) -> None:
        """ResourceNotFoundError should format correctly."""
        error = ResourceNotFoundError("User", "user-123")
        assert error.resource_type == "User"
        assert error.resource_id == "user-123"
        assert "User not found" in str(error)
        assert "user-123" in str(error)

    def test_resource_already_exists(self) -> None:
        """ResourceAlreadyExistsError should format correctly."""
        error = ResourceAlreadyExistsError("Portfolio", "portfolio-456")
        assert "Portfolio already exists" in str(error)
        assert error.code == ErrorCode.RESOURCE_ALREADY_EXISTS


class TestNetworkErrors:
    """Tests for network errors."""

    def test_network_errors_recoverable_by_default(self) -> None:
        """Network errors should be recoverable by default."""
        error = NetworkError("Network issue")
        assert error.recoverable is True

    def test_connection_error(self) -> None:
        """ConnectionError should track service."""
        error = ConnectionError("CoinGecko API")
        assert error.service == "CoinGecko API"
        assert "CoinGecko API" in str(error)

    def test_timeout_error(self) -> None:
        """TimeoutError should track timeout duration."""
        error = TimeoutError("fetch_prices", timeout_seconds=30.0, service="Binance")
        assert error.timeout_seconds == 30.0
        assert "30" in str(error)
        assert "fetch_prices" in str(error)

    def test_rate_limit_error(self) -> None:
        """RateLimitError should track retry_after."""
        error = RateLimitError("CoinGecko", retry_after=60)
        assert error.retry_after == 60
        assert "60" in str(error)
        assert error.context.metadata["retry_after"] == 60

    def test_api_error(self) -> None:
        """APIError should track status code."""
        error = APIError("CoinGecko", status_code=429, response_body='{"error": "rate limited"}')
        assert error.status_code == 429
        assert error.response_body == '{"error": "rate limited"}'
        assert "429" in str(error)


class TestDatabaseErrors:
    """Tests for database errors."""

    def test_query_error(self) -> None:
        """QueryError should not log full queries."""
        error = QueryError("Query failed", query="SELECT * FROM users WHERE id=1")
        # Should only log query type, not full query
        assert error.context.metadata.get("query_type") == "SELECT"

    def test_transaction_error(self) -> None:
        """TransactionError should be recoverable."""
        error = TransactionError()
        assert error.recoverable is True
        assert error.code == ErrorCode.TRANSACTION_FAILED


class TestCryptoErrors:
    """Tests for crypto/trading errors."""

    def test_insufficient_funds_error(self) -> None:
        """InsufficientFundsError should track amounts."""
        error = InsufficientFundsError(required=100.0, available=50.0, currency="BTC")
        assert error.required == 100.0
        assert error.available == 50.0
        assert error.currency == "BTC"
        assert "100" in str(error)
        assert "50" in str(error)
        assert "BTC" in str(error)

    def test_invalid_symbol_error(self) -> None:
        """InvalidSymbolError should track symbol."""
        error = InvalidSymbolError("INVALID")
        assert error.symbol == "INVALID"
        assert "INVALID" in str(error)

    def test_trade_error(self) -> None:
        """TradeError should track trade type."""
        error = TradeError("Trade rejected", symbol="BTC", trade_type="market_buy")
        assert error.trade_type == "market_buy"
        assert error.symbol == "BTC"

    def test_portfolio_error(self) -> None:
        """PortfolioError should track portfolio ID."""
        error = PortfolioError("Portfolio calculation failed", portfolio_id="pf-123")
        assert error.portfolio_id == "pf-123"


class TestSecurityErrors:
    """Tests for security errors."""

    def test_security_errors_not_recoverable(self) -> None:
        """Security errors should never be recoverable."""
        errors = [
            SecurityError("Security breach"),
            EncryptionError(),
            DecryptionError(),
            SecurityPolicyViolationError("password_policy"),
        ]
        for error in errors:
            assert error.recoverable is False

    def test_security_errors_critical_severity(self) -> None:
        """Security errors should be critical by default."""
        error = SecurityError("Security issue")
        assert error.severity == ErrorSeverity.CRITICAL

    def test_security_policy_violation(self) -> None:
        """SecurityPolicyViolationError should track policy."""
        error = SecurityPolicyViolationError("min_password_length", details="Password too short")
        assert error.policy == "min_password_length"
        assert "min_password_length" in str(error)
        assert "Password too short" in str(error)


class TestAgentErrors:
    """Tests for agent/skill errors."""

    def test_skill_not_found(self) -> None:
        """SkillNotFoundError should track skill name."""
        error = SkillNotFoundError("analyze_portfolio")
        assert error.skill_name == "analyze_portfolio"
        assert "analyze_portfolio" in str(error)

    def test_skill_execution_error(self) -> None:
        """SkillExecutionError should chain cause."""
        cause = ValueError("Invalid data")
        error = SkillExecutionError("analyze_market", cause=cause)
        assert error.skill_name == "analyze_market"
        assert error.cause is cause
        assert error.recoverable is True

    def test_cognitive_error(self) -> None:
        """CognitiveError should have correct code."""
        error = CognitiveError("Cognitive processing failed")
        assert error.code == ErrorCode.COGNITIVE_ERROR


class TestConfigurationErrors:
    """Tests for configuration errors."""

    def test_configuration_error(self) -> None:
        """ConfigurationError should track config key."""
        error = ConfigurationError("Invalid config", config_key="database.host")
        assert error.config_key == "database.host"
        assert error.recoverable is False

    def test_initialization_error(self) -> None:
        """InitializationError should track component."""
        error = InitializationError("DatabasePool")
        assert error.component == "DatabasePool"
        assert "DatabasePool" in str(error)


class TestWrapException:
    """Tests for wrap_exception utility function."""

    def test_wrap_standard_exception(self) -> None:
        """wrap_exception should wrap standard exceptions."""
        original = ValueError("Bad value")
        wrapped = wrap_exception(original)
        assert isinstance(wrapped, CoinbaseError)
        assert wrapped.cause is original
        assert "Bad value" in wrapped.message

    def test_wrap_with_custom_message(self) -> None:
        """wrap_exception should accept custom message."""
        original = ValueError("Bad value")
        wrapped = wrap_exception(original, message="Custom message")
        assert wrapped.message == "Custom message"

    def test_wrap_with_code(self) -> None:
        """wrap_exception should accept error code."""
        original = ValueError("Bad value")
        wrapped = wrap_exception(original, code=ErrorCode.VALIDATION_ERROR)
        assert wrapped.code == ErrorCode.VALIDATION_ERROR

    def test_wrap_coinbase_error_returns_same(self) -> None:
        """wrap_exception should return CoinbaseError unchanged."""
        original = CoinbaseError("Already wrapped")
        wrapped = wrap_exception(original)
        assert wrapped is original


class TestIsRecoverable:
    """Tests for is_recoverable utility function."""

    def test_coinbase_error_recoverable(self) -> None:
        """is_recoverable should check CoinbaseError.recoverable."""
        recoverable = NetworkError("Network issue", recoverable=True)
        not_recoverable = AuthenticationError()

        assert is_recoverable(recoverable) is True
        assert is_recoverable(not_recoverable) is False

    def test_standard_exception_transient_patterns(self) -> None:
        """is_recoverable should detect transient patterns."""
        transient_errors = [
            Exception("Connection timeout"),
            Exception("Rate limit exceeded"),
            Exception("Network error occurred"),
            Exception("Temporary failure"),
        ]
        for error in transient_errors:
            assert is_recoverable(error) is True

    def test_standard_exception_not_transient(self) -> None:
        """is_recoverable should return False for non-transient errors."""
        errors = [
            ValueError("Invalid input"),
            KeyError("missing_key"),
            TypeError("Type mismatch"),
        ]
        for error in errors:
            assert is_recoverable(error) is False


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_coinbase_error(self) -> None:
        """All custom exceptions should inherit from CoinbaseError."""
        # Create instances of each exception type and verify inheritance
        exceptions: list[CoinbaseError] = [
            ValidationError("Test message"),
            InvalidInputError("Test message"),
            AuthError("Test message"),
            AuthenticationError(),
            ResourceError("Test message"),
            ResourceNotFoundError("User", "123"),
            NetworkError("Test message"),
            ConnectionError("TestService"),
            DatabaseError("Test message"),
            CryptoError("Test message"),
            SecurityError("Test message"),
            AgentError("Test message"),
            ConfigurationError("Test message"),
            MissingFieldError("field"),
        ]
        for error in exceptions:
            assert isinstance(error, CoinbaseError)
            assert isinstance(error, Exception)

    def test_exception_catching(self) -> None:
        """Exceptions should be catchable by parent class."""
        try:
            raise InvalidInputError("Bad input")
        except ValidationError as e:
            assert isinstance(e, InvalidInputError)
        except Exception:
            pytest.fail("Should have been caught by ValidationError")

        try:
            raise SkillNotFoundError("skill")
        except AgentError as e:
            assert isinstance(e, SkillNotFoundError)
        except Exception:
            pytest.fail("Should have been caught by AgentError")
