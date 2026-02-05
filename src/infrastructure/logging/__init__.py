"""Structured logging with correlation IDs for parasitic leak remediation."""

import logging
import logging.handlers
from contextvars import ContextVar
from typing import Any

# Context variable for correlation ID
_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with correlation ID support.

    Args:
        name: Logger name

    Returns:
        Logger instance with correlation ID support
    """
    logger = logging.getLogger(name)

    # Add correlation ID filter if not already present
    if not any(isinstance(f, CorrelationIdFilter) for f in logger.filters):
        logger.addFilter(CorrelationIdFilter())

    return logger


def set_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation ID for the current context.

    Args:
        correlation_id: Correlation ID to set
    """
    _correlation_id.set(correlation_id)


def get_correlation_id() -> str | None:
    """
    Get the current correlation ID.

    Returns:
        Current correlation ID or None
    """
    return _correlation_id.get()


class CorrelationIdFilter(logging.Filter):
    """Filter that adds correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record."""
        correlation_id = _correlation_id.get()
        if correlation_id:
            record.correlation_id = correlation_id
        else:
            record.correlation_id = "none"
        return True


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs."""

    def __init__(self) -> None:
        super().__init__()
        self.default_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - correlation_id=%(correlation_id)s - %(message)s"
        )

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with correlation ID."""
        return self.default_formatter.format(record)


__all__ = [
    "get_logger",
    "set_correlation_id",
    "get_correlation_id",
    "CorrelationIdFilter",
    "StructuredFormatter",
]
