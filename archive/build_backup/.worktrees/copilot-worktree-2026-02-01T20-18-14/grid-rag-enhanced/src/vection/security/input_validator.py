"""Input Validator - Comprehensive input sanitization and validation.

Provides input validation and sanitization for all VECTION operations.
Prevents injection attacks, data corruption, and malicious payloads.

Features:
- String validation and sanitization
- Metadata validation with key/value constraints
- Session ID format validation
- Signal ID format validation
- Path traversal prevention
- HTML/script injection prevention
- Size limit enforcement
- Type validation
- Integration with audit logging

Usage:
    from vection.security.input_validator import InputValidator, ValidationResult

    validator = InputValidator()

    # Validate metadata
    result = validator.validate_metadata(user_provided_metadata)
    if not result.is_valid:
        raise ValidationError(result.errors)

    # Sanitize string input
    safe_string = validator.sanitize_string(user_input)

    # Validate session ID format
    if not validator.is_valid_session_id(session_id):
        raise ValidationError("Invalid session ID format")
"""

from __future__ import annotations

import html
import logging
import re
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from re import Pattern
from typing import Any

logger = logging.getLogger(__name__)


class ValidationErrorType(str, Enum):
    """Types of validation errors."""

    INVALID_TYPE = "invalid_type"
    INVALID_FORMAT = "invalid_format"
    INVALID_LENGTH = "invalid_length"
    INVALID_VALUE = "invalid_value"
    FORBIDDEN_CONTENT = "forbidden_content"
    PATH_TRAVERSAL = "path_traversal"
    INJECTION_ATTEMPT = "injection_attempt"
    SIZE_EXCEEDED = "size_exceeded"
    MISSING_REQUIRED = "missing_required"
    FORBIDDEN_KEY = "forbidden_key"
    NESTED_TOO_DEEP = "nested_too_deep"


class ValidationError(Exception):
    """Exception raised when validation fails.

    Attributes:
        errors: List of validation error details.
        field_name: Name of the field that failed validation.
    """

    def __init__(
        self,
        message: str,
        errors: list[dict[str, Any]] | None = None,
        field_name: str | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Error message.
            errors: List of validation error details.
            field_name: Name of the invalid field.
        """
        super().__init__(message)
        self.errors = errors or []
        self.field_name = field_name

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses.

        Returns:
            Dictionary with validation error details.
        """
        return {
            "error": "validation_error",
            "message": str(self),
            "field_name": self.field_name,
            "errors": self.errors,
        }


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Attributes:
        is_valid: Whether validation passed.
        errors: List of validation error details.
        sanitized_value: The sanitized value (if applicable).
        warnings: Non-fatal warnings.
    """

    is_valid: bool
    errors: list[dict[str, Any]] = field(default_factory=list)
    sanitized_value: Any = None
    warnings: list[str] = field(default_factory=list)

    def add_error(
        self,
        error_type: ValidationErrorType,
        field_name: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Add a validation error.

        Args:
            error_type: Type of validation error.
            field_name: Name of the invalid field.
            message: Error message.
            details: Additional error details.
        """
        self.is_valid = False
        self.errors.append(
            {
                "type": error_type.value,
                "field": field_name,
                "message": message,
                "details": details or {},
            }
        )

    def add_warning(self, message: str) -> None:
        """Add a non-fatal warning.

        Args:
            message: Warning message.
        """
        self.warnings.append(message)

    def merge(self, other: ValidationResult) -> ValidationResult:
        """Merge another validation result into this one.

        Args:
            other: Another validation result.

        Returns:
            Self for chaining.
        """
        if not other.is_valid:
            self.is_valid = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


@dataclass
class InputValidatorConfig:
    """Configuration for the input validator.

    Attributes:
        max_string_length: Maximum allowed string length.
        max_metadata_keys: Maximum keys in metadata dict.
        max_metadata_depth: Maximum nesting depth in metadata.
        max_metadata_value_length: Maximum length for metadata values.
        max_list_items: Maximum items in a list value.
        allowed_session_id_pattern: Regex pattern for valid session IDs.
        allowed_signal_id_pattern: Regex pattern for valid signal IDs.
        forbidden_keys: Keys that are not allowed in metadata.
        forbidden_patterns: Regex patterns that indicate injection attempts.
        enable_logging: Whether to log validation events.
    """

    max_string_length: int = 10000
    max_metadata_keys: int = 50
    max_metadata_depth: int = 5
    max_metadata_value_length: int = 1000
    max_list_items: int = 100
    allowed_session_id_pattern: str = r"^[a-zA-Z0-9_-]{1,64}$"
    allowed_signal_id_pattern: str = r"^[a-zA-Z0-9_-]{1,64}$"
    forbidden_keys: set[str] = field(
        default_factory=lambda: {
            "__proto__",
            "constructor",
            "prototype",
            "__class__",
            "__bases__",
            "__globals__",
            "__builtins__",
            "__import__",
            "__code__",
            "__reduce__",
            "__reduce_ex__",
        }
    )
    forbidden_patterns: list[str] = field(
        default_factory=lambda: [
            r"<script[^>]*>",  # Script tags
            r"javascript:",  # JavaScript URLs
            r"on\w+\s*=",  # Event handlers
            r"\{\{.*\}\}",  # Template injection
            r"\$\{.*\}",  # Template literals
            r"eval\s*\(",  # eval calls
            r"exec\s*\(",  # exec calls
            r"__import__\s*\(",  # Python imports
            r"\.\./",  # Path traversal
            r"\.\.\\",  # Windows path traversal
        ]
    )
    enable_logging: bool = True


class InputValidator:
    """Comprehensive input validator and sanitizer.

    Provides validation and sanitization for all user-provided inputs
    to prevent injection attacks and ensure data integrity.

    Thread-safe and suitable for concurrent use.

    Usage:
        validator = InputValidator()

        # Validate metadata
        result = validator.validate_metadata(data)
        if not result.is_valid:
            return error_response(result.errors)

        # Get sanitized value
        safe_data = result.sanitized_value
    """

    def __init__(self, config: InputValidatorConfig | None = None) -> None:
        """Initialize the input validator.

        Args:
            config: Validator configuration.
        """
        self.config = config or InputValidatorConfig()
        self._lock = threading.Lock()

        # Compile regex patterns
        self._session_id_pattern: Pattern[str] = re.compile(self.config.allowed_session_id_pattern)
        self._signal_id_pattern: Pattern[str] = re.compile(self.config.allowed_signal_id_pattern)
        self._forbidden_patterns: list[Pattern[str]] = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.config.forbidden_patterns
        ]

        # Statistics
        self._total_validations = 0
        self._total_failures = 0
        self._total_sanitizations = 0

        # Audit logger (lazy loaded)
        self._audit_logger: Any = None

        # Custom validators
        self._custom_validators: dict[str, Callable[[Any], ValidationResult]] = {}

    def validate_string(
        self,
        value: Any,
        field_name: str = "string",
        max_length: int | None = None,
        min_length: int = 0,
        pattern: Pattern[str] | str | None = None,
        allow_empty: bool = True,
        sanitize: bool = True,
    ) -> ValidationResult:
        """Validate a string value.

        Args:
            value: Value to validate.
            field_name: Name of the field (for error messages).
            max_length: Maximum allowed length (None for config default).
            min_length: Minimum required length.
            pattern: Regex pattern the string must match.
            allow_empty: Whether empty strings are allowed.
            sanitize: Whether to sanitize the string.

        Returns:
            ValidationResult with validation status and sanitized value.
        """
        result = ValidationResult(is_valid=True)
        max_len = max_length or self.config.max_string_length

        # Type check
        if not isinstance(value, str):
            result.add_error(
                ValidationErrorType.INVALID_TYPE,
                field_name,
                f"Expected string, got {type(value).__name__}",
            )
            return result

        # Empty check
        if not value and not allow_empty:
            result.add_error(
                ValidationErrorType.MISSING_REQUIRED,
                field_name,
                "Value cannot be empty",
            )
            return result

        # Length checks
        if len(value) > max_len:
            result.add_error(
                ValidationErrorType.INVALID_LENGTH,
                field_name,
                f"String exceeds maximum length of {max_len}",
                {"actual_length": len(value), "max_length": max_len},
            )
            return result

        if len(value) < min_length:
            result.add_error(
                ValidationErrorType.INVALID_LENGTH,
                field_name,
                f"String must be at least {min_length} characters",
                {"actual_length": len(value), "min_length": min_length},
            )
            return result

        # Pattern check
        if pattern is not None:
            if isinstance(pattern, str):
                pattern = re.compile(pattern)
            if not pattern.match(value):
                result.add_error(
                    ValidationErrorType.INVALID_FORMAT,
                    field_name,
                    "String does not match required pattern",
                )
                return result

        # Forbidden pattern check
        for forbidden in self._forbidden_patterns:
            if forbidden.search(value):
                result.add_error(
                    ValidationErrorType.INJECTION_ATTEMPT,
                    field_name,
                    "String contains forbidden pattern",
                )
                self._log_validation_failure(field_name, "injection_attempt", value[:100])
                return result

        # Sanitize if requested
        if sanitize:
            result.sanitized_value = self.sanitize_string(value)
        else:
            result.sanitized_value = value

        self._total_validations += 1
        return result

    def validate_session_id(self, value: Any, field_name: str = "session_id") -> ValidationResult:
        """Validate a session ID.

        Args:
            value: Value to validate.
            field_name: Name of the field.

        Returns:
            ValidationResult with validation status.
        """
        result = ValidationResult(is_valid=True)

        if not isinstance(value, str):
            result.add_error(
                ValidationErrorType.INVALID_TYPE,
                field_name,
                f"Session ID must be a string, got {type(value).__name__}",
            )
            return result

        if not self._session_id_pattern.match(value):
            result.add_error(
                ValidationErrorType.INVALID_FORMAT,
                field_name,
                "Invalid session ID format",
                {"pattern": self.config.allowed_session_id_pattern},
            )
            return result

        result.sanitized_value = value
        self._total_validations += 1
        return result

    def validate_signal_id(self, value: Any, field_name: str = "signal_id") -> ValidationResult:
        """Validate a signal ID.

        Args:
            value: Value to validate.
            field_name: Name of the field.

        Returns:
            ValidationResult with validation status.
        """
        result = ValidationResult(is_valid=True)

        if not isinstance(value, str):
            result.add_error(
                ValidationErrorType.INVALID_TYPE,
                field_name,
                f"Signal ID must be a string, got {type(value).__name__}",
            )
            return result

        if not self._signal_id_pattern.match(value):
            result.add_error(
                ValidationErrorType.INVALID_FORMAT,
                field_name,
                "Invalid signal ID format",
                {"pattern": self.config.allowed_signal_id_pattern},
            )
            return result

        result.sanitized_value = value
        self._total_validations += 1
        return result

    def validate_metadata(
        self,
        value: Any,
        field_name: str = "metadata",
        max_depth: int | None = None,
        current_depth: int = 0,
    ) -> ValidationResult:
        """Validate metadata dictionary.

        Args:
            value: Value to validate.
            field_name: Name of the field.
            max_depth: Maximum nesting depth.
            current_depth: Current nesting depth (internal use).

        Returns:
            ValidationResult with validation status and sanitized value.
        """
        result = ValidationResult(is_valid=True)
        max_depth = max_depth or self.config.max_metadata_depth

        # Type check
        if not isinstance(value, dict):
            result.add_error(
                ValidationErrorType.INVALID_TYPE,
                field_name,
                f"Metadata must be a dictionary, got {type(value).__name__}",
            )
            return result

        # Depth check
        if current_depth > max_depth:
            result.add_error(
                ValidationErrorType.NESTED_TOO_DEEP,
                field_name,
                f"Metadata exceeds maximum nesting depth of {max_depth}",
            )
            return result

        # Key count check
        if len(value) > self.config.max_metadata_keys:
            result.add_error(
                ValidationErrorType.SIZE_EXCEEDED,
                field_name,
                f"Metadata exceeds maximum key count of {self.config.max_metadata_keys}",
            )
            return result

        sanitized: dict[str, Any] = {}

        for key, val in value.items():
            # Validate key
            if not isinstance(key, str):
                result.add_error(
                    ValidationErrorType.INVALID_TYPE,
                    f"{field_name}.key",
                    "Metadata keys must be strings",
                )
                continue

            # Check forbidden keys
            if key.lower() in {k.lower() for k in self.config.forbidden_keys}:
                result.add_error(
                    ValidationErrorType.FORBIDDEN_KEY,
                    f"{field_name}.{key}",
                    f"Key '{key}' is not allowed in metadata",
                )
                self._log_validation_failure(field_name, "forbidden_key", key)
                continue

            # Validate and sanitize key
            key_result = self.validate_string(
                key,
                f"{field_name}.key",
                max_length=256,
                allow_empty=False,
            )
            if not key_result.is_valid:
                result.merge(key_result)
                continue

            safe_key = key_result.sanitized_value

            # Validate value based on type
            val_result = self._validate_metadata_value(
                val,
                f"{field_name}.{key}",
                max_depth,
                current_depth,
            )

            if not val_result.is_valid:
                result.merge(val_result)
            else:
                sanitized[safe_key] = val_result.sanitized_value

        result.sanitized_value = sanitized
        self._total_validations += 1
        return result

    def _validate_metadata_value(
        self,
        value: Any,
        field_name: str,
        max_depth: int,
        current_depth: int,
    ) -> ValidationResult:
        """Validate a metadata value of any type.

        Args:
            value: Value to validate.
            field_name: Name of the field.
            max_depth: Maximum nesting depth.
            current_depth: Current nesting depth.

        Returns:
            ValidationResult with validation status and sanitized value.
        """
        result = ValidationResult(is_valid=True)

        if value is None:
            result.sanitized_value = None
            return result

        if isinstance(value, bool):
            result.sanitized_value = value
            return result

        if isinstance(value, (int, float)):
            result.sanitized_value = value
            return result

        if isinstance(value, str):
            str_result = self.validate_string(
                value,
                field_name,
                max_length=self.config.max_metadata_value_length,
            )
            return str_result

        if isinstance(value, list):
            return self._validate_list(value, field_name, max_depth, current_depth)

        if isinstance(value, dict):
            return self.validate_metadata(value, field_name, max_depth, current_depth + 1)

        # Unsupported type - convert to string
        result.add_warning(f"Converted unsupported type {type(value).__name__} to string")
        result.sanitized_value = self.sanitize_string(str(value))
        return result

    def _validate_list(
        self,
        value: list[Any],
        field_name: str,
        max_depth: int,
        current_depth: int,
    ) -> ValidationResult:
        """Validate a list value.

        Args:
            value: List to validate.
            field_name: Name of the field.
            max_depth: Maximum nesting depth.
            current_depth: Current nesting depth.

        Returns:
            ValidationResult with validation status and sanitized value.
        """
        result = ValidationResult(is_valid=True)

        if len(value) > self.config.max_list_items:
            result.add_error(
                ValidationErrorType.SIZE_EXCEEDED,
                field_name,
                f"List exceeds maximum item count of {self.config.max_list_items}",
            )
            return result

        sanitized: list[Any] = []

        for i, item in enumerate(value):
            item_result = self._validate_metadata_value(
                item,
                f"{field_name}[{i}]",
                max_depth,
                current_depth,
            )
            if not item_result.is_valid:
                result.merge(item_result)
            else:
                sanitized.append(item_result.sanitized_value)

        result.sanitized_value = sanitized
        return result

    def validate_event_payload(
        self,
        payload: Any,
        field_name: str = "payload",
    ) -> ValidationResult:
        """Validate an event payload.

        Args:
            payload: Payload to validate.
            field_name: Name of the field.

        Returns:
            ValidationResult with validation status and sanitized value.
        """
        result = ValidationResult(is_valid=True)

        if payload is None:
            result.sanitized_value = {}
            return result

        if not isinstance(payload, dict):
            result.add_error(
                ValidationErrorType.INVALID_TYPE,
                field_name,
                f"Payload must be a dictionary, got {type(payload).__name__}",
            )
            return result

        # Validate as metadata with stricter limits
        return self.validate_metadata(payload, field_name)

    def sanitize_string(self, value: str) -> str:
        """Sanitize a string value.

        Removes or escapes potentially dangerous content.

        Args:
            value: String to sanitize.

        Returns:
            Sanitized string.
        """
        if not value:
            return value

        self._total_sanitizations += 1

        # HTML escape
        sanitized = html.escape(value)

        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")

        # Remove other control characters (except newline, tab, carriage return)
        sanitized = "".join(char for char in sanitized if ord(char) >= 32 or char in "\n\t\r")

        # Normalize whitespace
        sanitized = " ".join(sanitized.split())

        return sanitized

    def sanitize_path(self, value: str) -> str:
        """Sanitize a file path to prevent traversal.

        Args:
            value: Path to sanitize.

        Returns:
            Sanitized path.
        """
        if not value:
            return value

        # Remove path traversal sequences
        sanitized = value.replace("..", "")
        sanitized = sanitized.replace("\\", "/")

        # Remove leading slashes
        sanitized = sanitized.lstrip("/")

        # Remove any remaining dangerous patterns
        sanitized = re.sub(r"[<>:\"|?*]", "", sanitized)

        return sanitized

    def is_valid_session_id(self, value: Any) -> bool:
        """Quick check if a session ID is valid.

        Args:
            value: Value to check.

        Returns:
            True if valid, False otherwise.
        """
        if not isinstance(value, str):
            return False
        return bool(self._session_id_pattern.match(value))

    def is_valid_signal_id(self, value: Any) -> bool:
        """Quick check if a signal ID is valid.

        Args:
            value: Value to check.

        Returns:
            True if valid, False otherwise.
        """
        if not isinstance(value, str):
            return False
        return bool(self._signal_id_pattern.match(value))

    def register_custom_validator(
        self,
        name: str,
        validator: Callable[[Any], ValidationResult],
    ) -> None:
        """Register a custom validator.

        Args:
            name: Validator name.
            validator: Validation function.
        """
        with self._lock:
            self._custom_validators[name] = validator

    def run_custom_validator(self, name: str, value: Any) -> ValidationResult:
        """Run a custom validator.

        Args:
            name: Validator name.
            value: Value to validate.

        Returns:
            ValidationResult.

        Raises:
            KeyError: If validator not found.
        """
        with self._lock:
            if name not in self._custom_validators:
                raise KeyError(f"Custom validator '{name}' not found")
            return self._custom_validators[name](value)

    def require_valid(self, result: ValidationResult, field_name: str = "input") -> None:
        """Raise exception if validation failed.

        Args:
            result: Validation result to check.
            field_name: Field name for error message.

        Raises:
            ValidationError: If validation failed.
        """
        if not result.is_valid:
            raise ValidationError(
                f"Validation failed for {field_name}",
                errors=result.errors,
                field_name=field_name,
            )

    def get_stats(self) -> dict[str, Any]:
        """Get validator statistics.

        Returns:
            Dictionary with statistics.
        """
        return {
            "total_validations": self._total_validations,
            "total_failures": self._total_failures,
            "total_sanitizations": self._total_sanitizations,
            "failure_rate_percent": (
                round((self._total_failures / self._total_validations) * 100, 2) if self._total_validations > 0 else 0
            ),
            "custom_validators": list(self._custom_validators.keys()),
        }

    def _log_validation_failure(
        self,
        field_name: str,
        reason: str,
        value_preview: str,
    ) -> None:
        """Log a validation failure to audit logger."""
        self._total_failures += 1

        if not self.config.enable_logging:
            return

        try:
            if self._audit_logger is None:
                from vection.security.audit_logger import get_audit_logger

                self._audit_logger = get_audit_logger()

            self._audit_logger.log_validation_event(
                passed=False,
                session_id=None,
                field_name=field_name,
                reason=reason,
                original_value=value_preview[:100] if value_preview else None,
            )
        except Exception:
            # Don't let logging failures break validation
            pass


# Module-level singleton
_input_validator: InputValidator | None = None


def get_input_validator(config: InputValidatorConfig | None = None) -> InputValidator:
    """Get the global input validator instance.

    Args:
        config: Configuration (only used on first call).

    Returns:
        InputValidator singleton.
    """
    global _input_validator
    if _input_validator is None:
        _input_validator = InputValidator(config)
    return _input_validator
