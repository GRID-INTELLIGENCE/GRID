"""Comprehensive logging configuration for the Coinbase platform.

This module provides:
- Structured logging with JSON format
- Log rotation and file management
- Correlation IDs for request tracking
- Sensitive data masking
- Multiple log handlers (console, file, JSON)
- Environment-aware logging levels

Usage:
    from coinbase.logging_config import setup_logging, get_logger

    # Setup logging at application start
    setup_logging(level="INFO", json_output=True)

    # Get a logger for your module
    logger = get_logger(__name__)
    logger.info("Operation completed", extra={"user_id": "hashed_id", "action": "trade"})
"""

import json
import logging
import os
import re
import sys
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable

# Context variable for correlation ID (thread-safe)
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


# =============================================================================
# Sensitive Data Patterns
# =============================================================================

# Patterns for sensitive data that should be masked in logs
SENSITIVE_PATTERNS = [
    # API keys and tokens
    (
        re.compile(r'(?i)(api[_-]?key|apikey)["\s:=]+["\']?([a-zA-Z0-9_\-]{16,})["\']?'),
        r'\1="[REDACTED]"',
    ),
    (
        re.compile(r'(?i)(token|bearer)["\s:=]+["\']?([a-zA-Z0-9_\-\.]{16,})["\']?'),
        r'\1="[REDACTED]"',
    ),
    (
        re.compile(r'(?i)(secret|password|passwd|pwd)["\s:=]+["\']?([^\s"\']{4,})["\']?'),
        r'\1="[REDACTED]"',
    ),
    # Email addresses
    (re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"), "[EMAIL_REDACTED]"),
    # Credit card numbers (basic pattern)
    (re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b"), "[CARD_REDACTED]"),
    # Private keys
    (
        re.compile(r'(?i)(private[_-]?key)["\s:=]+["\']?([a-zA-Z0-9+/=]{32,})["\']?'),
        r'\1="[REDACTED]"',
    ),
    # AWS credentials
    (
        re.compile(r'(?i)(aws[_-]?access[_-]?key[_-]?id)["\s:=]+["\']?([A-Z0-9]{16,})["\']?'),
        r'\1="[REDACTED]"',
    ),
    (
        re.compile(r'(?i)(aws[_-]?secret)["\s:=]+["\']?([a-zA-Z0-9+/]{32,})["\']?'),
        r'\1="[REDACTED]"',
    ),
]

# Fields that should never be logged
SENSITIVE_FIELDS = frozenset(
    [
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "private_key",
        "privatekey",
        "credit_card",
        "creditcard",
        "ssn",
        "social_security",
        "auth_token",
        "refresh_token",
        "access_token",
    ]
)


def mask_sensitive_data(message: str) -> str:
    """Mask sensitive data in log messages.

    Args:
        message: The log message to sanitize

    Returns:
        Sanitized message with sensitive data masked
    """
    if not isinstance(message, str):
        message = str(message)

    for pattern, replacement in SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)

    return message


def mask_dict_values(data: dict[str, Any], depth: int = 0, max_depth: int = 10) -> dict[str, Any]:
    """Recursively mask sensitive values in a dictionary.

    Args:
        data: Dictionary to sanitize
        depth: Current recursion depth
        max_depth: Maximum recursion depth

    Returns:
        Dictionary with sensitive values masked
    """
    if depth > max_depth:
        return {"[MAX_DEPTH_EXCEEDED]": True}

    result = {}
    for key, value in data.items():
        key_lower = key.lower().replace("-", "_")

        if key_lower in SENSITIVE_FIELDS:
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = mask_dict_values(value, depth + 1, max_depth)  # type: ignore
        elif isinstance(value, list):
            result[key] = [  # type: ignore
                mask_dict_values(v, depth + 1, max_depth) if isinstance(v, dict) else v
                for v in value
            ]
        elif isinstance(value, str):
            result[key] = mask_sensitive_data(value)
        else:
            result[key] = value

    return result


# =============================================================================
# Correlation ID Management
# =============================================================================


def get_correlation_id() -> str:
    """Get the current correlation ID.

    Returns:
        The current correlation ID or empty string if not set
    """
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str | None = None) -> str:
    """Set a correlation ID for the current context.

    Args:
        correlation_id: Optional ID to set. Generates UUID if not provided.

    Returns:
        The correlation ID that was set
    """
    cid = correlation_id or str(uuid.uuid4())
    correlation_id_var.set(cid)
    return cid


def clear_correlation_id() -> None:
    """Clear the correlation ID for the current context."""
    correlation_id_var.set("")


# =============================================================================
# Custom Log Formatters
# =============================================================================


class SensitiveDataFilter(logging.Filter):
    """Filter that masks sensitive data in log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Mask sensitive data in the log record."""
        # Mask the message
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = mask_sensitive_data(record.msg)

        # Mask args if they exist
        if record.args:
            if isinstance(record.args, dict):
                record.args = mask_dict_values(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    mask_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )

        return True


class CorrelationIdFilter(logging.Filter):
    """Filter that adds correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to the log record."""
        record.correlation_id = get_correlation_id() or "-"
        return True


class StandardFormatter(logging.Formatter):
    """Standard text formatter with timestamps and context."""

    DEFAULT_FORMAT = (
        "%(asctime)s | %(levelname)-8s | %(correlation_id)s | %(name)s:%(lineno)d | %(message)s"
    )

    def __init__(self, fmt: str | None = None, datefmt: str | None = None):
        super().__init__(fmt=fmt or self.DEFAULT_FORMAT, datefmt=datefmt or "%Y-%m-%d %H:%M:%S")


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(
        self,
        include_timestamp: bool = True,
        include_level: bool = True,
        include_logger: bool = True,
        include_path: bool = True,
        include_correlation_id: bool = True,
        extra_fields: dict[str, Any] | None = None,
    ):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_logger = include_logger
        self.include_path = include_path
        self.include_correlation_id = include_correlation_id
        self.extra_fields = extra_fields or {}

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_data: dict[str, Any] = {}

        if self.include_timestamp:
            log_data["timestamp"] = datetime.now(UTC).isoformat() + "Z"

        if self.include_level:
            log_data["level"] = record.levelname
            log_data["level_num"] = record.levelno

        if self.include_logger:
            log_data["logger"] = record.name

        if self.include_path:
            log_data["path"] = f"{record.pathname}:{record.lineno}"
            log_data["function"] = record.funcName

        if self.include_correlation_id:
            log_data["correlation_id"] = getattr(record, "correlation_id", "-")

        # Add the message
        log_data["message"] = record.getMessage()

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "correlation_id",
                "message",
                "taskName",
            ):
                if not key.startswith("_"):
                    log_data[key] = value

        # Add configured extra fields
        log_data.update(self.extra_fields)

        # Mask sensitive data in the entire log entry
        log_data = mask_dict_values(log_data)

        return json.dumps(log_data, default=str, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, fmt: str | None = None, datefmt: str | None = None):
        super().__init__(
            fmt=fmt or StandardFormatter.DEFAULT_FORMAT, datefmt=datefmt or "%Y-%m-%d %H:%M:%S"
        )

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors."""
        # Save original levelname
        original_levelname = record.levelname

        # Add color
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"

        # Format
        result = super().format(record)

        # Restore original
        record.levelname = original_levelname

        return result


# =============================================================================
# Log Configuration
# =============================================================================


@dataclass
class LogConfig:
    """Configuration for logging setup."""

    level: str = "INFO"
    json_output: bool = False
    log_dir: str = "logs"
    max_file_size_mb: int = 10
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = True
    enable_colors: bool = True
    app_name: str = "coinbase"
    environment: str = "development"
    extra_fields: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "LogConfig":
        """Create LogConfig from environment variables."""
        return cls(
            level=os.environ.get("LOG_LEVEL", "INFO").upper(),
            json_output=os.environ.get("LOG_JSON", "false").lower() == "true",
            log_dir=os.environ.get("LOG_DIR", "logs"),
            max_file_size_mb=int(os.environ.get("LOG_MAX_SIZE_MB", "10")),
            backup_count=int(os.environ.get("LOG_BACKUP_COUNT", "5")),
            enable_console=os.environ.get("LOG_CONSOLE", "true").lower() == "true",
            enable_file=os.environ.get("LOG_FILE", "true").lower() == "true",
            enable_colors=os.environ.get("LOG_COLORS", "true").lower() == "true",
            app_name=os.environ.get("APP_NAME", "coinbase"),
            environment=os.environ.get("ENVIRONMENT", "development"),
        )


def setup_logging(
    level: str = "INFO",
    json_output: bool = False,
    log_dir: str = "logs",
    max_file_size_mb: int = 10,
    backup_count: int = 5,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_colors: bool = True,
    app_name: str = "coinbase",
    config: LogConfig | None = None,
) -> None:
    """Set up logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Use JSON format for logs
        log_dir: Directory for log files
        max_file_size_mb: Maximum size of each log file in MB
        backup_count: Number of backup files to keep
        enable_console: Enable console logging
        enable_file: Enable file logging
        enable_colors: Enable colored console output (ignored if json_output=True)
        app_name: Application name for log identification
        config: Optional LogConfig object (overrides other parameters)
    """
    if config:
        level = config.level
        json_output = config.json_output
        log_dir = config.log_dir
        max_file_size_mb = config.max_file_size_mb
        backup_count = config.backup_count
        enable_console = config.enable_console
        enable_file = config.enable_file
        enable_colors = config.enable_colors
        app_name = config.app_name

    # Get or create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create filters (will be added to each handler)
    sensitive_filter = SensitiveDataFilter()
    correlation_filter = CorrelationIdFilter()

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))

        if json_output:
            console_handler.setFormatter(
                JSONFormatter(extra_fields={"app": app_name, "output": "console"})
            )
        elif enable_colors and sys.stdout.isatty():
            console_handler.setFormatter(ColoredFormatter())
        else:
            console_handler.setFormatter(StandardFormatter())

        # Add filters to handler (ensures correlation_id is set before formatting)
        console_handler.addFilter(correlation_filter)
        console_handler.addFilter(sensitive_filter)
        root_logger.addHandler(console_handler)

    # File handler
    if enable_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Regular log file
        log_file = log_path / f"{app_name}.log"
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, level.upper()))

        if json_output:
            file_handler.setFormatter(
                JSONFormatter(extra_fields={"app": app_name, "output": "file"})
            )
        else:
            file_handler.setFormatter(StandardFormatter())

        # Add filters to handler
        file_handler.addFilter(correlation_filter)
        file_handler.addFilter(sensitive_filter)
        root_logger.addHandler(file_handler)

        # Error log file (errors and above only)
        error_file = log_path / f"{app_name}.error.log"
        error_handler = RotatingFileHandler(
            filename=str(error_file),
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)

        if json_output:
            error_handler.setFormatter(
                JSONFormatter(extra_fields={"app": app_name, "output": "error_file"})
            )
        else:
            error_handler.setFormatter(StandardFormatter())

        # Add filters to handler
        error_handler.addFilter(correlation_filter)
        error_handler.addFilter(sensitive_filter)
        root_logger.addHandler(error_handler)

    # Log startup message
    root_logger.info(
        f"Logging initialized: level={level}, json={json_output}, "
        f"console={enable_console}, file={enable_file}"
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the specified module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# =============================================================================
# Context Manager for Correlation IDs
# =============================================================================


class LogContext:
    """Context manager for setting correlation ID during a block of code.

    Usage:
        with LogContext(correlation_id="request-123"):
            logger.info("Processing request")
            # All logs in this block will have the correlation ID
    """

    def __init__(self, correlation_id: str | None = None, **extra: Any):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.extra = extra
        self.previous_id: str = ""

    def __enter__(self) -> "LogContext":
        self.previous_id = get_correlation_id()
        set_correlation_id(self.correlation_id)
        return self

    def __exit__(self, *args: Any) -> None:
        if self.previous_id:
            set_correlation_id(self.previous_id)
        else:
            clear_correlation_id()


# =============================================================================
# Utility Functions
# =============================================================================


def log_execution_time(logger: logging.Logger, operation: str) -> Callable:
    """Decorator to log execution time of a function.

    Args:
        logger: Logger to use
        operation: Name of the operation for logging
    """
    import time
    from functools import wraps

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.info(
                    f"{operation} completed",
                    extra={"elapsed_ms": round(elapsed_ms, 2), "status": "success"},
                )
                return result
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.error(
                    f"{operation} failed: {e}",
                    extra={"elapsed_ms": round(elapsed_ms, 2), "status": "error"},
                )
                raise

        return wrapper

    return decorator


__all__ = [
    # Configuration
    "LogConfig",
    "setup_logging",
    "get_logger",
    # Correlation ID
    "get_correlation_id",
    "set_correlation_id",
    "clear_correlation_id",
    "LogContext",
    # Formatters
    "StandardFormatter",
    "JSONFormatter",
    "ColoredFormatter",
    # Filters
    "SensitiveDataFilter",
    "CorrelationIdFilter",
    # Utilities
    "mask_sensitive_data",
    "mask_dict_values",
    "log_execution_time",
]
