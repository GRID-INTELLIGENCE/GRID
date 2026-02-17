"""
Security Decorators for GRID.

Provides decorators for:
- Audit logging of high-risk operations
- Input validation and sanitization
- Path validation enforcement
- Security event tracking

Usage:
    from grid.security.decorators import (
        audit_high_risk_operation,
        validate_input,
        require_path_validation,
    )

    @audit_high_risk_operation(operation_type="subprocess")
    def run_command(cmd: str) -> str:
        ...

    @validate_input
    def process_file(filename: str) -> None:
        ...

    @require_path_validation(base_path="/app/data")
    def read_file(file_path: str) -> str:
        ...
"""

from __future__ import annotations

import functools
import inspect
import logging
from pathlib import Path
from typing import Any, Callable, TypeVar

from .audit_logger import AuditEventType, AuditLogger
from .input_sanitizer import InputSanitizer
from .path_validator import PathValidator, SecurityError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def audit_high_risk_operation(
    operation_type: str = "unknown",
    log_args: bool = True,
    log_result: bool = False,
    redact_sensitive: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to audit high-risk operations.

    Logs function calls with arguments and results for security auditing.

    Args:
        operation_type: Type of operation (e.g., "subprocess", "file_operation", "deserialization")
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        redact_sensitive: Whether to redact sensitive arguments (passwords, tokens, etc.)

    Returns:
        Decorated function

    Example:
        @audit_high_risk_operation(operation_type="subprocess")
        def execute_command(cmd: list[str]) -> str:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get audit logger
            audit_logger = AuditLogger()

            # Prepare log data
            log_data: dict[str, Any] = {
                "operation_type": operation_type,
                "function": f"{func.__module__}.{func.__qualname__}",
            }

            # Log arguments if enabled
            if log_args:
                if redact_sensitive:
                    log_data["args"] = _redact_sensitive_args(args, kwargs)
                else:
                    log_data["args"] = _format_args(args, kwargs)

            try:
                # Execute function
                result = func(*args, **kwargs)

                # Log result if enabled
                if log_result:
                    log_data["result"] = _format_result(result, redact_sensitive)

                log_data["success"] = True

                # Log successful operation
                audit_logger.log_event(
                    event_type=AuditEventType.SECRET_ACCESS,  # Using existing event type
                    details=log_data,
                )

                return result

            except Exception as e:
                log_data["success"] = False
                log_data["error"] = str(e)
                log_data["error_type"] = type(e).__name__

                # Log failed operation
                audit_logger.log_event(
                    event_type=AuditEventType.SECRET_ACCESS,
                    details=log_data,
                )

                # Re-raise exception
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


def validate_input(
    sanitize: bool = True,
    max_length: int | None = None,
    allowed_chars: str | None = None,
) -> Callable[[F], F]:
    """
    Decorator to validate and sanitize function inputs.

    Validates string inputs and optionally sanitizes them using InputSanitizer.

    Args:
        sanitize: Whether to sanitize inputs
        max_length: Maximum length for string inputs
        allowed_chars: Allowed characters pattern (regex)

    Returns:
        Decorated function

    Example:
        @validate_input(sanitize=True, max_length=100)
        def process_user_input(text: str) -> str:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Get sanitizer if needed
            sanitizer = InputSanitizer() if sanitize else None

            # Validate and sanitize arguments
            validated_args = []
            validated_kwargs = {}

            for param_name, param_value in bound_args.arguments.items():
                param = sig.parameters[param_name]

                # Only validate string parameters
                if isinstance(param_value, str):
                    # Check max length
                    if max_length and len(param_value) > max_length:
                        raise ValueError(f"Input '{param_name}' exceeds maximum length of {max_length}")

                    # Check allowed characters
                    if allowed_chars:
                        import re

                        if not re.match(allowed_chars, param_value):
                            raise ValueError(f"Input '{param_name}' contains invalid characters")

                    # Sanitize if enabled
                    if sanitizer:
                        param_value = sanitizer.sanitize(param_value)

                # Store validated value
                if param.kind == inspect.Parameter.VAR_KEYWORD:
                    validated_kwargs.update(param_value if isinstance(param_value, dict) else {})
                elif param.kind == inspect.Parameter.VAR_POSITIONAL:
                    validated_args.extend(param_value if isinstance(param_value, (list, tuple)) else [param_value])
                elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                    validated_kwargs[param_name] = param_value
                else:
                    validated_args.append(param_value)

            # Call function with validated arguments
            return func(*validated_args, **validated_kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def require_path_validation(
    base_path: str | Path,
    param_name: str = "path",
    must_exist: bool = False,
) -> Callable[[F], F]:
    """
    Decorator to enforce path validation.

    Validates that file paths are within allowed base directory.

    Args:
        base_path: Base directory that paths must be within
        param_name: Name of the parameter containing the path
        must_exist: Whether the path must exist

    Returns:
        Decorated function

    Example:
        @require_path_validation(base_path="/app/data", param_name="file_path")
        def read_file(file_path: str) -> str:
            ...
    """
    base = Path(base_path).resolve()

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Get path parameter value
            if param_name not in bound_args.arguments:
                raise ValueError(f"Parameter '{param_name}' not found in function signature")

            path_value = bound_args.arguments[param_name]

            if not path_value:
                raise ValueError(f"Path parameter '{param_name}' is empty")

            # Validate path
            try:
                if must_exist:
                    validated_path = PathValidator.validate_file_exists(path_value, base)
                else:
                    validated_path = PathValidator.validate_path(path_value, base)

                # Replace path in arguments
                bound_args.arguments[param_name] = str(validated_path)

                # Call function with validated path
                return func(*bound_args.args, **bound_args.kwargs)

            except SecurityError as e:
                logger.warning(f"Path validation failed: {e}")
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


def _redact_sensitive_args(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive information from function arguments."""
    sensitive_keys = {
        "password",
        "passwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "auth",
        "credential",
        "key",
    }

    redacted_args = []
    for arg in args:
        if isinstance(arg, str) and any(key in str(arg).lower() for key in sensitive_keys):
            redacted_args.append("***REDACTED***")
        elif isinstance(arg, (dict, list)):
            redacted_args.append(_redact_dict_or_list(arg))
        else:
            redacted_args.append(str(arg)[:100] if len(str(arg)) > 100 else str(arg))

    redacted_kwargs = {}
    for key, value in kwargs.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            redacted_kwargs[key] = "***REDACTED***"
        elif isinstance(value, (dict, list)):
            redacted_kwargs[key] = _redact_dict_or_list(value)
        elif isinstance(value, str) and len(value) > 100:
            redacted_kwargs[key] = value[:100] + "..."
        else:
            redacted_kwargs[key] = value

    return {"args": redacted_args, "kwargs": redacted_kwargs}


def _redact_dict_or_list(obj: dict[str, Any] | list[Any]) -> dict[str, Any] | list[Any]:
    """Recursively redact sensitive data from dict or list."""
    if isinstance(obj, dict):
        return {
            k: "***REDACTED***"
            if any(s in k.lower() for s in ["password", "secret", "token", "key"])
            else _redact_dict_or_list(v)
            if isinstance(v, (dict, list))
            else v
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [_redact_dict_or_list(item) if isinstance(item, (dict, list)) else item for item in obj]
    return obj


def _format_args(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    """Format function arguments for logging."""
    return {
        "args": [str(arg)[:200] if len(str(arg)) > 200 else str(arg) for arg in args],
        "kwargs": {k: str(v)[:200] if len(str(v)) > 200 else str(v) for k, v in kwargs.items()},
    }


def _format_result(result: Any, redact_sensitive: bool) -> Any:
    """Format function result for logging."""
    if redact_sensitive and isinstance(result, (dict, list)):
        return _redact_dict_or_list(result)
    elif isinstance(result, str) and len(result) > 500:
        return result[:500] + "..."
    return result
