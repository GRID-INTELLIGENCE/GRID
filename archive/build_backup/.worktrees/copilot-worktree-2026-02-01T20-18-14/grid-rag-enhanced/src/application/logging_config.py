"""
Logging configuration for GRID Application Layer.

Provides standardized logging configuration and utilities
for all application modules (Mothership, Resonance, etc.).

All modules should use this configuration to ensure consistent
logging patterns across the application.
"""

from __future__ import annotations

import logging
import sys


def setup_logging(
    level: int = logging.INFO,
    format_string: str | None = None,
    handlers: list | None = None,
) -> None:
    """
    Setup logging configuration for the application.

    This function should be called once at application startup.
    Individual modules should use logging.getLogger(__name__) to
    get their logger instance.

    Args:
        level: Logging level (default: INFO)
        format_string: Custom format string (default: standard format)
        handlers: Custom handlers (default: StreamHandler to stdout)
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    if handlers is None:
        handlers = [logging.StreamHandler(sys.stdout)]

    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=handlers,
        force=True,  # Override any existing configuration
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    This is a convenience function that ensures consistent
    logger creation. Modules should use:
        logger = logging.getLogger(__name__)

    Or alternatively:
        from application.logging_config import get_logger
        logger = get_logger(__name__)

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Standard logging pattern:
# 1. Import logging at module level: import logging
# 2. Get logger: logger = logging.getLogger(__name__)
# 3. Use logger: logger.info("message"), logger.error("message", exc_info=True)
#
# Example:
#   import logging
#   logger = logging.getLogger(__name__)
#   logger.info("Module initialized")
#   logger.error("Error occurred", exc_info=True)

__all__ = [
    "setup_logging",
    "get_logger",
]
