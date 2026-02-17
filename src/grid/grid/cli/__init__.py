"""GRID CLI Module

Provides CLI-specific utilities and error classes.
"""

from __future__ import annotations


class FileIngestionError(Exception):
    """Raised when file ingestion fails."""

    pass


class CLIConfigurationError(Exception):
    """Raised when CLI configuration is invalid."""

    pass


class CommandExecutionError(Exception):
    """Raised when command execution fails."""

    pass
