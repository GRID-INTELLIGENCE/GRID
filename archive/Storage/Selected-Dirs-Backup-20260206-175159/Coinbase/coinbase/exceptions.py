"""Custom exception hierarchy for the Coinbase platform.

This module provides a comprehensive exception system with:
- Hierarchical exception classes
- Error codes for categorization
- Context tracking for debugging
- Structured error responses
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from typing import Any


class ErrorCode(Enum):
    """Error codes for categorizing exceptions."""

    # General errors (1000-1999)
    UNKNOWN_ERROR = 1000
    INTERNAL_ERROR = 1001
    NOT_IMPLEMENTED = 1002
    CONFIGURATION_ERROR = 1003
    INITIALIZATION_ERROR = 1004
    SHUTDOWN_ERROR = 1005

    # Validation errors (2000-2999)
    VALIDATION_ERROR = 2000
    INVALID_INPUT = 2001
    INVALID_FORMAT = 2002
    MISSING_REQUIRED_FIELD = 2003
    VALUE_OUT_OF_RANGE = 2004
    TYPE_MISMATCH = 2005
    SCHEMA_VALIDATION_FAILED = 2006

    # Authentication/Authorization errors (3000-3999)
    AUTH_ERROR = 3000
    AUTHENTICATION_FAILED = 3001
    AUTHORIZATION_FAILED = 3002
    TOKEN_EXPIRED = 3003
    TOKEN_INVALID = 3004
    PERMISSION_DENIED = 3005
    ACCESS_DENIED = 3006

    # Resource errors (4000-4999)
    RESOURCE_ERROR = 4000
    RESOURCE_NOT_FOUND = 4001
    RESOURCE_ALREADY_EXISTS = 4002
    RESOURCE_CONFLICT = 4003
    RESOURCE_LOCKED = 4004
    RESOURCE_EXHAUSTED = 4005

    # Network/External service errors (5000-5999)
    NETWORK_ERROR = 5000
    CONNECTION_FAILED = 5001
    CONNECTION_TIMEOUT = 5002
    REQUEST_TIMEOUT = 5003
    SERVICE_UNAVAILABLE = 5004
    RATE_LIMITED = 5005
    API_ERROR = 5006

    # Database errors (6000-6999)
    DATABASE_ERROR = 6000
    QUERY_FAILED = 6001
    TRANSACTION_FAILED = 6002
    CONSTRAINT_VIOLATION = 6003
    DEADLOCK_DETECTED = 6004
    CONNECTION_POOL_EXHAUSTED = 6005

    # Crypto/Trading errors (7000-7999)
    CRYPTO_ERROR = 7000
    INSUFFICIENT_FUNDS = 7001
    INVALID_SYMBOL = 7002
    TRADE_FAILED = 7003
    PRICE_CHANGED = 7004
    ORDER_REJECTED = 7005
    MARKET_CLOSED = 7006
    PORTFOLIO_ERROR = 7007

    # Security errors (8000-8999)
    SECURITY_ERROR = 8000
    ENCRYPTION_FAILED = 8001
    DECRYPTION_FAILED = 8002
    SIGNATURE_INVALID = 8003
    HASH_MISMATCH = 8004
    SECURITY_POLICY_VIOLATION = 8005

    # Agent/Skill errors (9000-9999)
    AGENT_ERROR = 9000
    SKILL_NOT_FOUND = 9001
    SKILL_EXECUTION_FAILED = 9002
    SKILL_TIMEOUT = 9003
    AGENT_INITIALIZATION_FAILED = 9004
    COGNITIVE_ERROR = 9005


class ErrorSeverity(Enum):
    """Severity levels for exceptions."""

    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class ErrorContext:
    """Context information for debugging errors."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    component: str | None = None
    operation: str | None = None
    user_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    stack_trace: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for logging/serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "component": self.component,
            "operation": self.operation,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
            "stack_trace": self.stack_trace,
        }


class CoinbaseError(Exception):
    """Base exception for all Coinbase platform errors.

    All custom exceptions should inherit from this class.

    Attributes:
        message: Human-readable error message
        code: Error code for categorization
        severity: Severity level of the error
        recoverable: Whether the error is potentially recoverable
        context: Additional context for debugging
        cause: The underlying exception that caused this error
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        recoverable: bool = False,
        context: ErrorContext | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.severity = severity
        self.recoverable = recoverable
        self.context = context or ErrorContext()
        self.cause = cause

        if cause is not None:
            self.__cause__ = cause

    def with_context(self, **kwargs: Any) -> "CoinbaseError":
        """Add context information to the error.

        Returns self for method chaining.
        """
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
            else:
                self.context.metadata[key] = value
        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        result = {
            "error": True,
            "code": self.code.value,
            "code_name": self.code.name,
            "message": self.message,
            "severity": self.severity.name,
            "recoverable": self.recoverable,
            "context": self.context.to_dict(),
        }

        if self.cause:
            result["cause"] = str(self.cause)

        return result

    def __str__(self) -> str:
        return f"[{self.code.name}] {self.message}"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"code={self.code.name}, "
            f"severity={self.severity.name}, "
            f"recoverable={self.recoverable})"
        )


# =============================================================================
# Validation Errors
# =============================================================================


class ValidationError(CoinbaseError):
    """Base class for validation-related errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.VALIDATION_ERROR,
        field: str | None = None,
        value: Any = None,
        **kwargs: Any,
    ):
        super().__init__(message, code=code, **kwargs)
        self.field = field
        self.value = value
        self.context.metadata["field"] = field
        self.context.metadata["value"] = repr(value) if value is not None else None


class InvalidInputError(ValidationError):
    """Raised when input data is invalid."""

    def __init__(self, message: str, field: str | None = None, value: Any = None, **kwargs: Any):
        super().__init__(message, code=ErrorCode.INVALID_INPUT, field=field, value=value, **kwargs)


class MissingFieldError(ValidationError):
    """Raised when a required field is missing."""

    def __init__(self, field: str, **kwargs: Any):
        super().__init__(
            f"Missing required field: {field}",
            code=ErrorCode.MISSING_REQUIRED_FIELD,
            field=field,
            **kwargs,
        )


class ValueOutOfRangeError(ValidationError):
    """Raised when a value is outside acceptable range."""

    def __init__(
        self,
        field: str,
        value: Any,
        min_value: Any = None,
        max_value: Any = None,
        **kwargs: Any,
    ):
        range_desc = []
        if min_value is not None:
            range_desc.append(f"min={min_value}")
        if max_value is not None:
            range_desc.append(f"max={max_value}")

        range_str = ", ".join(range_desc) if range_desc else "unspecified"
        message = f"Value {value} for field '{field}' is out of range ({range_str})"

        super().__init__(
            message, code=ErrorCode.VALUE_OUT_OF_RANGE, field=field, value=value, **kwargs
        )
        self.min_value = min_value
        self.max_value = max_value


# =============================================================================
# Authentication/Authorization Errors
# =============================================================================


class AuthError(CoinbaseError):
    """Base class for authentication/authorization errors."""

    def __init__(self, message: str, code: ErrorCode = ErrorCode.AUTH_ERROR, **kwargs: Any):
        super().__init__(message, code=code, recoverable=False, **kwargs)


class AuthenticationError(AuthError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", **kwargs: Any):
        super().__init__(message, code=ErrorCode.AUTHENTICATION_FAILED, **kwargs)


class AuthorizationError(AuthError):
    """Raised when authorization fails."""

    def __init__(
        self, message: str = "Authorization failed", resource: str | None = None, **kwargs: Any
    ):
        super().__init__(message, code=ErrorCode.AUTHORIZATION_FAILED, **kwargs)
        self.resource = resource
        if resource:
            self.context.metadata["resource"] = resource


class PermissionDeniedError(AuthError):
    """Raised when permission is denied for an operation."""

    def __init__(self, operation: str, resource: str | None = None, **kwargs: Any):
        message = f"Permission denied for operation: {operation}"
        if resource:
            message += f" on resource: {resource}"
        super().__init__(message, code=ErrorCode.PERMISSION_DENIED, **kwargs)
        self.operation = operation
        self.resource = resource


# =============================================================================
# Resource Errors
# =============================================================================


class ResourceError(CoinbaseError):
    """Base class for resource-related errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.RESOURCE_ERROR,
        resource_type: str | None = None,
        resource_id: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(message, code=code, **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id
        if resource_type:
            self.context.metadata["resource_type"] = resource_type
        if resource_id:
            self.context.metadata["resource_id"] = resource_id


class ResourceNotFoundError(ResourceError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: str, **kwargs: Any):
        message = f"{resource_type} not found: {resource_id}"
        super().__init__(
            message,
            code=ErrorCode.RESOURCE_NOT_FOUND,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs,
        )


class ResourceAlreadyExistsError(ResourceError):
    """Raised when attempting to create a resource that already exists."""

    def __init__(self, resource_type: str, resource_id: str, **kwargs: Any):
        message = f"{resource_type} already exists: {resource_id}"
        super().__init__(
            message,
            code=ErrorCode.RESOURCE_ALREADY_EXISTS,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs,
        )


# =============================================================================
# Network/External Service Errors
# =============================================================================


class NetworkError(CoinbaseError):
    """Base class for network-related errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.NETWORK_ERROR,
        service: str | None = None,
        **kwargs: Any,
    ):
        kwargs.setdefault("recoverable", True)
        super().__init__(message, code=code, **kwargs)
        self.service = service
        if service:
            self.context.metadata["service"] = service


class ConnectionError(NetworkError):
    """Raised when a connection cannot be established."""

    def __init__(self, service: str, message: str | None = None, **kwargs: Any):
        msg = message or f"Failed to connect to {service}"
        super().__init__(msg, code=ErrorCode.CONNECTION_FAILED, service=service, **kwargs)


class TimeoutError(NetworkError):
    """Raised when an operation times out."""

    def __init__(
        self,
        operation: str,
        timeout_seconds: float | None = None,
        service: str | None = None,
        **kwargs: Any,
    ):
        message = f"Operation '{operation}' timed out"
        if timeout_seconds:
            message += f" after {timeout_seconds}s"
        super().__init__(message, code=ErrorCode.REQUEST_TIMEOUT, service=service, **kwargs)
        self.timeout_seconds = timeout_seconds


class RateLimitError(NetworkError):
    """Raised when rate limited by an external service."""

    def __init__(
        self,
        service: str,
        retry_after: int | None = None,
        **kwargs: Any,
    ):
        message = f"Rate limited by {service}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, code=ErrorCode.RATE_LIMITED, service=service, **kwargs)
        self.retry_after = retry_after
        if retry_after:
            self.context.metadata["retry_after"] = retry_after


class APIError(NetworkError):
    """Raised when an external API returns an error."""

    def __init__(
        self,
        service: str,
        status_code: int | None = None,
        response_body: str | None = None,
        **kwargs: Any,
    ):
        message = f"API error from {service}"
        if status_code:
            message += f" (HTTP {status_code})"
        super().__init__(message, code=ErrorCode.API_ERROR, service=service, **kwargs)
        self.status_code = status_code
        self.response_body = response_body
        if status_code:
            self.context.metadata["status_code"] = status_code


# =============================================================================
# Database Errors
# =============================================================================


class DatabaseError(CoinbaseError):
    """Base class for database-related errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.DATABASE_ERROR,
        query: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(message, code=code, **kwargs)
        # Never log full queries in production - they may contain sensitive data
        if query:
            self.context.metadata["query_type"] = query.split()[0] if query else None


class QueryError(DatabaseError):
    """Raised when a database query fails."""

    def __init__(self, message: str, query: str | None = None, **kwargs: Any):
        super().__init__(message, code=ErrorCode.QUERY_FAILED, query=query, **kwargs)


class TransactionError(DatabaseError):
    """Raised when a database transaction fails."""

    def __init__(self, message: str = "Transaction failed", **kwargs: Any):
        super().__init__(message, code=ErrorCode.TRANSACTION_FAILED, recoverable=True, **kwargs)


# =============================================================================
# Crypto/Trading Errors
# =============================================================================


class CryptoError(CoinbaseError):
    """Base class for crypto/trading-related errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.CRYPTO_ERROR,
        symbol: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(message, code=code, **kwargs)
        self.symbol = symbol
        if symbol:
            self.context.metadata["symbol"] = symbol


class InsufficientFundsError(CryptoError):
    """Raised when there are insufficient funds for an operation."""

    def __init__(
        self,
        required: float,
        available: float,
        currency: str,
        **kwargs: Any,
    ):
        message = (
            f"Insufficient funds: required {required} {currency}, available {available} {currency}"
        )
        super().__init__(message, code=ErrorCode.INSUFFICIENT_FUNDS, **kwargs)
        self.required = required
        self.available = available
        self.currency = currency


class InvalidSymbolError(CryptoError):
    """Raised when an invalid crypto symbol is provided."""

    def __init__(self, symbol: str, **kwargs: Any):
        message = f"Invalid crypto symbol: {symbol}"
        super().__init__(message, code=ErrorCode.INVALID_SYMBOL, symbol=symbol, **kwargs)


class TradeError(CryptoError):
    """Raised when a trade operation fails."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        trade_type: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(message, code=ErrorCode.TRADE_FAILED, symbol=symbol, **kwargs)
        self.trade_type = trade_type
        if trade_type:
            self.context.metadata["trade_type"] = trade_type


class PortfolioError(CryptoError):
    """Raised when a portfolio operation fails."""

    def __init__(self, message: str, portfolio_id: str | None = None, **kwargs: Any):
        super().__init__(message, code=ErrorCode.PORTFOLIO_ERROR, **kwargs)
        self.portfolio_id = portfolio_id
        if portfolio_id:
            self.context.metadata["portfolio_id"] = portfolio_id


# =============================================================================
# Security Errors
# =============================================================================


class SecurityError(CoinbaseError):
    """Base class for security-related errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.SECURITY_ERROR,
        **kwargs: Any,
    ):
        # Security errors are never recoverable and always critical
        kwargs["recoverable"] = False
        kwargs.setdefault("severity", ErrorSeverity.CRITICAL)
        super().__init__(message, code=code, **kwargs)


class EncryptionError(SecurityError):
    """Raised when encryption fails."""

    def __init__(self, message: str = "Encryption failed", **kwargs: Any):
        super().__init__(message, code=ErrorCode.ENCRYPTION_FAILED, **kwargs)


class DecryptionError(SecurityError):
    """Raised when decryption fails."""

    def __init__(self, message: str = "Decryption failed", **kwargs: Any):
        super().__init__(message, code=ErrorCode.DECRYPTION_FAILED, **kwargs)


class SecurityPolicyViolationError(SecurityError):
    """Raised when a security policy is violated."""

    def __init__(self, policy: str, details: str | None = None, **kwargs: Any):
        message = f"Security policy violation: {policy}"
        if details:
            message += f". {details}"
        super().__init__(message, code=ErrorCode.SECURITY_POLICY_VIOLATION, **kwargs)
        self.policy = policy


# =============================================================================
# Agent/Skill Errors
# =============================================================================


class AgentError(CoinbaseError):
    """Base class for agent-related errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.AGENT_ERROR,
        agent_id: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(message, code=code, **kwargs)
        self.agent_id = agent_id
        if agent_id:
            self.context.metadata["agent_id"] = agent_id


class SkillNotFoundError(AgentError):
    """Raised when a requested skill is not found."""

    def __init__(self, skill_name: str, **kwargs: Any):
        message = f"Skill not found: {skill_name}"
        super().__init__(message, code=ErrorCode.SKILL_NOT_FOUND, **kwargs)
        self.skill_name = skill_name


class SkillExecutionError(AgentError):
    """Raised when skill execution fails."""

    def __init__(
        self,
        skill_name: str,
        message: str | None = None,
        cause: Exception | None = None,
        **kwargs: Any,
    ):
        msg = message or f"Skill execution failed: {skill_name}"
        super().__init__(
            msg,
            code=ErrorCode.SKILL_EXECUTION_FAILED,
            cause=cause,
            recoverable=True,
            **kwargs,
        )
        self.skill_name = skill_name
        self.context.metadata["skill_name"] = skill_name


class CognitiveError(AgentError):
    """Raised when cognitive processing fails."""

    def __init__(self, message: str, **kwargs: Any):
        super().__init__(message, code=ErrorCode.COGNITIVE_ERROR, **kwargs)


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(CoinbaseError):
    """Raised when there's a configuration error."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(message, code=ErrorCode.CONFIGURATION_ERROR, recoverable=False, **kwargs)
        self.config_key = config_key
        if config_key:
            self.context.metadata["config_key"] = config_key


class InitializationError(CoinbaseError):
    """Raised when component initialization fails."""

    def __init__(self, component: str, message: str | None = None, **kwargs: Any):
        msg = message or f"Failed to initialize: {component}"
        super().__init__(msg, code=ErrorCode.INITIALIZATION_ERROR, recoverable=False, **kwargs)
        self.component = component
        self.context.metadata["component"] = component


# =============================================================================
# Utility Functions
# =============================================================================


def wrap_exception(
    exception: Exception,
    message: str | None = None,
    code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
    **kwargs: Any,
) -> CoinbaseError:
    """Wrap a standard exception in a CoinbaseError.

    Args:
        exception: The exception to wrap
        message: Optional custom message (defaults to str(exception))
        code: Error code to use
        **kwargs: Additional arguments for CoinbaseError

    Returns:
        A CoinbaseError wrapping the original exception
    """
    if isinstance(exception, CoinbaseError):
        return exception

    return CoinbaseError(
        message=message or str(exception),
        code=code,
        cause=exception,
        **kwargs,
    )


def is_recoverable(exception: Exception) -> bool:
    """Check if an exception is potentially recoverable.

    Args:
        exception: The exception to check

    Returns:
        True if the exception is recoverable, False otherwise
    """
    if isinstance(exception, CoinbaseError):
        return exception.recoverable

    # Check common transient error messages
    error_msg = str(exception).lower()
    transient_patterns = [
        "timeout",
        "timed out",
        "rate limit",
        "too many requests",
        "connection",
        "network",
        "temporary",
        "retry",
    ]

    return any(pattern in error_msg for pattern in transient_patterns)


__all__ = [
    # Enums
    "ErrorCode",
    "ErrorSeverity",
    # Context
    "ErrorContext",
    # Base
    "CoinbaseError",
    # Validation
    "ValidationError",
    "InvalidInputError",
    "MissingFieldError",
    "ValueOutOfRangeError",
    # Auth
    "AuthError",
    "AuthenticationError",
    "AuthorizationError",
    "PermissionDeniedError",
    # Resource
    "ResourceError",
    "ResourceNotFoundError",
    "ResourceAlreadyExistsError",
    # Network
    "NetworkError",
    "ConnectionError",
    "TimeoutError",
    "RateLimitError",
    "APIError",
    # Database
    "DatabaseError",
    "QueryError",
    "TransactionError",
    # Crypto
    "CryptoError",
    "InsufficientFundsError",
    "InvalidSymbolError",
    "TradeError",
    "PortfolioError",
    # Security
    "SecurityError",
    "EncryptionError",
    "DecryptionError",
    "SecurityPolicyViolationError",
    # Agent
    "AgentError",
    "SkillNotFoundError",
    "SkillExecutionError",
    "CognitiveError",
    # Configuration
    "ConfigurationError",
    "InitializationError",
    # Utilities
    "wrap_exception",
    "is_recoverable",
]
