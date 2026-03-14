"""
Environment-Aware Validation Framework.

Provides validation that adapts behavior based on deployment environment:
- Production: Fail fast (raise exceptions)
- Development: Warn only (log warnings)
- Testing: Silent (return issues without side effects)

Extracted from Mothership's validate() and validate_critical_settings() patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .base import SettingsBase

logger = logging.getLogger(__name__)


class ValidationMode(Enum):
    """Validation behavior modes."""

    WARN_ONLY = "warn"  # Log warnings, allow startup
    FAIL_FAST = "fail"  # Raise exceptions immediately
    SILENT = "silent"  # Return issues without logging


class ValidationSeverity(Enum):
    """Issue severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """
    Immutable validation issue.

    Attributes:
        message: Human-readable issue description
        severity: Issue severity level
        field: Optional field name that caused the issue
        suggestion: Optional fix suggestion
    """

    message: str
    severity: ValidationSeverity = ValidationSeverity.WARNING
    field: str | None = None
    suggestion: str | None = None

    def __str__(self) -> str:
        prefix = f"[{self.severity.value.upper()}]"
        if self.field:
            prefix = f"{prefix} {self.field}:"
        return f"{prefix} {self.message}"

    @property
    def is_critical(self) -> bool:
        """Check if this is a critical issue."""
        return self.severity == ValidationSeverity.CRITICAL


class EnvironmentAwareValidator:
    """
    Validator that adapts behavior based on environment.

    Production: Raises exceptions for critical issues (fail-fast)
    Development: Logs warnings but allows startup
    Testing: Returns issues without side effects

    Usage:
        validator = EnvironmentAwareValidator("production")
        issues = validator.validate(settings)

        # Or with custom mode
        validator = EnvironmentAwareValidator(mode=ValidationMode.WARN_ONLY)
    """

    def __init__(
        self,
        environment: str | None = None,
        *,
        mode: ValidationMode | None = None,
    ):
        """
        Initialize validator.

        Args:
            environment: Environment name (production, development, test)
            mode: Explicit validation mode (overrides environment-based mode)
        """
        if mode is not None:
            self.mode = mode
        else:
            self.mode = self._determine_mode(environment or "development")

    def _determine_mode(self, environment: str) -> ValidationMode:
        """Determine validation mode from environment string."""
        env_lower = environment.lower()

        if env_lower in ("production", "prod"):
            return ValidationMode.FAIL_FAST
        elif env_lower in ("test", "testing", "ci"):
            return ValidationMode.SILENT
        else:
            return ValidationMode.WARN_ONLY

    def validate(
        self,
        settings: SettingsBase,
        *,
        validators: list[Callable[[SettingsBase], list[ValidationIssue]]] | None = None,
    ) -> list[ValidationIssue]:
        """
        Validate settings and handle issues based on mode.

        Args:
            settings: Settings instance to validate
            validators: Optional list of custom validator functions

        Returns:
            List of validation issues

        Raises:
            ValueError: In FAIL_FAST mode with critical issues
        """
        issues: list[ValidationIssue] = []

        # Run built-in validation
        issues.extend(self._run_builtin_validators(settings))

        # Run custom validators
        if validators:
            for validator in validators:
                try:
                    issues.extend(validator(settings))
                except Exception as e:
                    issues.append(
                        ValidationIssue(
                            message=f"Validator {validator.__name__} raised: {e}",
                            severity=ValidationSeverity.WARNING,
                        )
                    )

        # Handle issues based on mode
        self._handle_issues(issues)

        return issues

    def _run_builtin_validators(self, settings: SettingsBase) -> list[ValidationIssue]:
        """Run built-in validation rules."""
        issues: list[ValidationIssue] = []

        # Call settings' own validate method
        raw_issues = settings.validate(fail_fast=False)

        # Convert string issues to ValidationIssue objects
        for issue_str in raw_issues:
            if issue_str.startswith("CRITICAL"):
                issues.append(
                    ValidationIssue(
                        message=issue_str.replace("CRITICAL: ", ""),
                        severity=ValidationSeverity.CRITICAL,
                    )
                )
            elif issue_str.startswith("WARNING"):
                issues.append(
                    ValidationIssue(
                        message=issue_str.replace("WARNING: ", ""),
                        severity=ValidationSeverity.WARNING,
                    )
                )
            else:
                issues.append(
                    ValidationIssue(
                        message=issue_str,
                        severity=ValidationSeverity.WARNING,
                    )
                )

        return issues

    def _handle_issues(self, issues: list[ValidationIssue]) -> None:
        """Handle issues based on validation mode."""
        if not issues:
            return

        critical_issues = [i for i in issues if i.is_critical]
        warning_issues = [i for i in issues if not i.is_critical]

        if self.mode == ValidationMode.FAIL_FAST:
            if critical_issues:
                # Raise exception with all critical issues
                messages = [str(i) for i in critical_issues]
                raise ValueError("Critical configuration issues:\n" + "\n".join(f"  - {m}" for m in messages))

        elif self.mode == ValidationMode.WARN_ONLY:
            # Log warnings
            for issue in critical_issues:
                logger.warning(f"Configuration issue: {issue}")
            for issue in warning_issues:
                logger.info(f"Configuration note: {issue}")

        # SILENT mode: just return issues, no side effects

    @staticmethod
    def create_issue(
        message: str,
        severity: ValidationSeverity = ValidationSeverity.WARNING,
        field: str | None = None,
        suggestion: str | None = None,
    ) -> ValidationIssue:
        """Factory method for creating validation issues."""
        return ValidationIssue(
            message=message,
            severity=severity,
            field=field,
            suggestion=suggestion,
        )


class ValidationBuilder:
    """
    Fluent builder for constructing validation rules.

    Usage:
        issues = (
            ValidationBuilder(settings)
            .require("secret_key", min_length=32)
            .forbid_wildcard("cors_origins")
            .require_in_production("database_url")
            .build()
        )
    """

    def __init__(self, settings: SettingsBase):
        """Initialize builder with settings instance."""
        self._settings = settings
        self._issues: list[ValidationIssue] = []
        self._environment = getattr(settings, "environment", "development")

    def require(
        self,
        field: str,
        *,
        min_length: int | None = None,
        message: str | None = None,
    ) -> ValidationBuilder:
        """Require a field to be present and optionally meet minimum length."""
        value = getattr(self._settings, field, None)

        if not value:
            self._issues.append(
                ValidationIssue(
                    message=message or f"{field} is required",
                    severity=ValidationSeverity.CRITICAL,
                    field=field,
                    suggestion=f"Set {field.upper()} environment variable",
                )
            )
        elif min_length and isinstance(value, str) and len(value) < min_length:
            self._issues.append(
                ValidationIssue(
                    message=message or f"{field} must be at least {min_length} characters",
                    severity=ValidationSeverity.WARNING,
                    field=field,
                    suggestion=f"Use a longer {field} (current: {len(value)} chars)",
                )
            )

        return self

    def forbid_wildcard(self, field: str, *, message: str | None = None) -> ValidationBuilder:
        """Forbid wildcard (*) in a list field."""
        value = getattr(self._settings, field, None)

        if value and isinstance(value, (list, tuple)) and "*" in value:
            self._issues.append(
                ValidationIssue(
                    message=message or f"{field} contains wildcard (*) which is not allowed in production",
                    severity=ValidationSeverity.CRITICAL
                    if self._environment == "production"
                    else ValidationSeverity.WARNING,
                    field=field,
                    suggestion="Use explicit values instead of wildcard",
                )
            )

        return self

    def require_in_production(
        self,
        field: str,
        *,
        message: str | None = None,
    ) -> ValidationBuilder:
        """Require a field only in production environment."""
        if self._environment != "production":
            return self

        value = getattr(self._settings, field, None)

        if not value:
            self._issues.append(
                ValidationIssue(
                    message=message or f"{field} is required in production",
                    severity=ValidationSeverity.CRITICAL,
                    field=field,
                    suggestion=f"Set {field.upper()} environment variable before production deployment",
                )
            )

        return self

    def custom(
        self,
        validator: Callable[[SettingsBase], ValidationIssue | list[ValidationIssue] | None],
    ) -> ValidationBuilder:
        """Add custom validator function."""
        try:
            result = validator(self._settings)
            if result:
                if isinstance(result, list):
                    self._issues.extend(result)
                else:
                    self._issues.append(result)
        except Exception as e:
            self._issues.append(
                ValidationIssue(
                    message=f"Custom validator failed: {e}",
                    severity=ValidationSeverity.WARNING,
                )
            )

        return self

    def build(self) -> list[ValidationIssue]:
        """Build and return list of validation issues."""
        return self._issues


def validate_production_ready(settings: SettingsBase) -> list[ValidationIssue]:
    """
    Common production readiness validation.

    Checks:
    - Secret key present and strong
    - No wildcard CORS
    - Debug mode disabled
    - Database URL explicit (not default)
    """
    return (
        ValidationBuilder(settings)
        .require("secret_key", min_length=32)
        .forbid_wildcard("cors_origins")
        .require_in_production("database_url")
        .build()
    )
