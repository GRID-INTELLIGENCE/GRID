"""GRID Safety Guardrails.

Provides mechanisms for command denylisting, environment blocking,
and execution safety checks with production-hardened security integration.
"""

from __future__ import annotations

import argparse
import os
from collections.abc import Callable
from functools import wraps
from typing import Any

from .config import safety_config


class GuardrailError(Exception):
    """Raised when a guardrail violation is detected."""

    pass


class SafetyGuardrails:
    """Manages command restrictions and environment checks.

    Provides static-like access to safety validation logic.
    """

    # Pre-calculated contribution scores based on architectural assessment
    CONTRIBUTION_SCORES: dict[str, float] = {
        "analyze": 0.75,  # Updated: Essential analysis tool
        "serve": 0.85,  # High signal server hub
        "process": 0.89,  # Core intelligence pipeline
        "skills": 0.91,  # High utility skill system
    }

    @classmethod
    def check_environment_lockdown(cls) -> None:
        """Check if the current environment allows execution."""
        # 1. Check for blocked environment variables
        for var in safety_config.blocked_env_vars:
            if os.getenv(var):
                raise GuardrailError(f"Execution blocked by environment variable: {var}")

        # 2. Check for required environment variables
        for var in safety_config.required_env_vars:
            if not os.getenv(var):
                raise GuardrailError(f"Missing required environment variable: {var}")

    @classmethod
    def validate_command(cls, command: str | None) -> None:
        """Check if the command is allowed."""
        if not command:
            return

        if command in safety_config.denylist:
            raise GuardrailError(f"Command '{command}' is currently on the denylist.")

        # Check contribution threshold if enabled
        if safety_config.check_contribution:
            score = cls.CONTRIBUTION_SCORES.get(command, 0.5)  # Default 0.5 for unknown commands
            if score < safety_config.contribution_threshold:
                raise GuardrailError(
                    f"Command '{command}' blocked. Contribution score {score:.2f} "
                    f"is below threshold {safety_config.contribution_threshold:.2f}."
                )

    @classmethod
    def run_all_checks(cls, command: str | None = None) -> None:
        """Convenience method to run all checks."""
        cls.check_environment_lockdown()
        if command:
            cls.validate_command(command)

    @classmethod
    def validate_production_security(cls, command: str | None = None) -> None:
        """Enhanced validation with production security manager."""
        try:
            # Import production security if available
            from ..security.production import security_manager

            # Validate environment
            validation = security_manager.validate_environment()
            if not validation["valid"]:
                for issue in validation["issues"]:
                    raise GuardrailError(f"Security validation failed: {issue}")

            # Check command with production rules
            if command:
                allowed, reason = security_manager.is_command_allowed(command)
                if not allowed:
                    raise GuardrailError(reason)

        except ImportError:
            # Fallback to basic validation if production security not available
            cls.run_all_checks(command)


def contribution_guard(func: Callable) -> Callable:
    """
    Wrapper to easily allow/block entity execution based on contribution.

    Can be applied to any function that takes 'args' with a 'command' attribute.
    """

    @wraps(func)
    def wrapper(args: argparse.Namespace, *func_args: Any, **func_kwargs: Any) -> Any:
        command = getattr(args, "command", None)

        # Try production security first
        try:
            SafetyGuardrails.validate_production_security(command)
        except GuardrailError:
            # Record failed attempt if production manager available
            try:
                from ..security.production import security_manager

                security_manager.record_failed_attempt()
            except ImportError:
                pass
            raise

        return func(args, *func_args, **func_kwargs)

    return wrapper


def production_guard(func: Callable) -> Callable:
    """
    Enhanced wrapper for production environments with comprehensive security checks.
    """

    @wraps(func)
    def wrapper(args: argparse.Namespace, *func_args: Any, **func_kwargs: Any) -> Any:
        command = getattr(args, "command", None)

        # Always use production security validation
        SafetyGuardrails.validate_production_security(command)

        # Reset failed attempts on success
        try:
            from ..security.production import security_manager

            security_manager.reset_failed_attempts()
        except ImportError:
            pass

        return func(args, *func_args, **func_kwargs)

    return wrapper
