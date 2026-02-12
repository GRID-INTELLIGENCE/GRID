"""
Structured Logging Configuration for GRID Mothership.

Provides production-grade structured logging using structlog,
configured for JSON output in production and colored console in development.

Usage:
    from application.mothership.logging_structured import get_logger

    logger = get_logger(__name__)
    logger.info("user_login", user_id="123", ip="127.0.0.1")
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

import structlog


def configure_structured_logging(
    environment: str = "development",
    log_level: str = "INFO",
    json_output: bool | None = None,
) -> None:
    """
    Configure structlog for the application.

    Args:
        environment: Current environment (development, production, testing)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Force JSON output. If None, auto-detect based on environment.
    """
    # Determine output format
    if json_output is None:
        json_output = environment.lower() in ("production", "staging")

    # Shared processors for all outputs
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        # Production: JSON output for log aggregation
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
        # Configure standard logging to also output JSON
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, log_level.upper(), logging.INFO),
        )
    else:
        # Development: Colored, human-readable output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
        logging.basicConfig(
            format="%(levelname)s %(name)s: %(message)s",
            stream=sys.stdout,
            level=getattr(logging, log_level.upper(), logging.INFO),
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog BoundLogger

    Example:
        logger = get_logger(__name__)
        logger.info("event_occurred", key="value", count=42)
    """
    return structlog.get_logger(name)


def bind_context(**context: Any) -> None:
    """
    Bind context variables that will be included in all subsequent log entries.

    Useful for adding request_id, user_id, etc. at the start of a request.

    Args:
        **context: Key-value pairs to bind

    Example:
        bind_context(request_id="abc-123", user_id="user-456")
        logger.info("processing")  # Includes request_id and user_id
    """
    structlog.contextvars.bind_contextvars(**context)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()


def unbind_context(*keys: str) -> None:
    """
    Remove specific keys from bound context.

    Args:
        *keys: Keys to remove
    """
    structlog.contextvars.unbind_contextvars(*keys)


# Auto-configure based on environment
_configured = False


def ensure_configured() -> None:
    """Ensure logging is configured (idempotent)."""
    global _configured
    if not _configured:
        env = os.getenv("MOTHERSHIP_ENVIRONMENT", "development")
        log_level = os.getenv("MOTHERSHIP_LOG_LEVEL", "INFO")
        configure_structured_logging(environment=env, log_level=log_level)
        _configured = True


# Export convenient access
__all__ = [
    "configure_structured_logging",
    "get_logger",
    "bind_context",
    "clear_context",
    "unbind_context",
    "ensure_configured",
]
