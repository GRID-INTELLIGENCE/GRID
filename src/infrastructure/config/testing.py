"""
Testing Utilities for Configuration.

Provides fixtures and helpers for testing configuration:
- Environment variable mocking
- Test settings factories
- Configuration assertions

Usage:
    from infrastructure.config.testing import test_settings, mock_env
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    from .base import SettingsBase


@dataclass(frozen=True, slots=True)
class TestConfig:
    """Immutable test configuration."""

    env: str = "test"
    database_url: str = "sqlite:///:memory:"
    secret_key: str = "test-secret-key-for-testing-only-32chars"
    debug: bool = True


@contextmanager
def mock_env(env_vars: dict[str, str]) -> Generator[dict[str, str]]:
    """
    Context manager to temporarily set environment variables.

    Args:
        env_vars: Dictionary of environment variables to set

    Yields:
        Dictionary of original values

    Examples:
        with mock_env({"MOTHERSHIP_ENVIRONMENT": "test"}):
            settings = Settings.from_env()
    """
    original: dict[str, str] = {}

    for key, value in env_vars.items():
        original[key] = os.environ.get(key, "")
        os.environ[key] = value

    try:
        yield original

    finally:
        # Restore original values
        for key, value in original.items():
            if value:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


@contextmanager
def test_settings_env(**overrides: str) -> Generator[dict[str, str]]:
    """
    Context manager with common test environment variables.

    Sets sensible defaults for testing:
    - ENVIRONMENT=test
    - DATABASE_URL=sqlite:///:memory:
    - SECRET_KEY=test-secret-key-for-testing-only-32chars
    - DEBUG=true

    Args:
        **overrides: Additional/override environment variables

    Yields:
        Dictionary of original values

    Examples:
        with test_settings_env(MOTHERSHIP_PORT="9000"):
            settings = Settings.from_env()
    """
    defaults = {
        "ENVIRONMENT": "test",
        "MOTHERSHIP_ENVIRONMENT": "test",
        "DATABASE_URL": "sqlite:///:memory:",
        "MOTHERSHIP_DATABASE_URL": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key-for-testing-only-32chars",
        "MOTHERSHIP_SECRET_KEY": "test-secret-key-for-testing-only-32chars",
        "DEBUG": "true",
        "MOTHERSHIP_DEBUG": "true",
    }

    # Apply overrides
    defaults.update(overrides)

    with mock_env(defaults) as original:
        yield original


@contextmanager
def production_env(**overrides: str) -> Generator[dict[str, str]]:
    """
    Context manager with production-like environment variables.

    Sets:
    - ENVIRONMENT=production
    - DEBUG=false
    - Required production settings

    Args:
        **overrides: Additional/override environment variables

    Yields:
        Dictionary of original values
    """
    defaults = {
        "ENVIRONMENT": "production",
        "MOTHERSHIP_ENVIRONMENT": "production",
        "DEBUG": "false",
        "MOTHERSHIP_DEBUG": "false",
        "DATABASE_URL": "postgresql://test:test@localhost/test",
        "MOTHERSHIP_DATABASE_URL": "postgresql://test:test@localhost/test",
        "SECRET_KEY": "production-strength-secret-key-for-testing-64-chars-minimum",
        "MOTHERSHIP_SECRET_KEY": "production-strength-secret-key-for-testing-64-chars-minimum",
    }

    defaults.update(overrides)

    with mock_env(defaults) as original:
        yield original


def create_test_settings(
    settings_class: type[SettingsBase],
    **overrides: Any,
) -> SettingsBase:
    """
    Create test settings instance with sensible defaults.

    Args:
        settings_class: Settings class to instantiate
        **overrides: Field overrides

    Returns:
        Settings instance with test defaults

    Examples:
        settings = create_test_settings(DatabaseSettings, pool_size=10)
    """
    with test_settings_env():
        return settings_class.from_env(**overrides)


def assert_validation_issues(
    settings: SettingsBase,
    *,
    expected_critical: int = 0,
    expected_warnings: int = 0,
    fail_fast: bool = False,
) -> list[str]:
    """
    Assert expected validation issues.

    Args:
        settings: Settings to validate
        expected_critical: Expected number of critical issues
        expected_warnings: Expected number of warnings
        fail_fast: Whether to use fail-fast mode

    Returns:
        List of issues

    Raises:
        AssertionError: If counts don't match
    """

    issues = settings.validate(fail_fast=fail_fast)

    critical = sum(1 for i in issues if "CRITICAL" in i.upper())
    warnings = sum(1 for i in issues if "WARNING" in i.upper() or "INFO" in i.upper())

    assert critical == expected_critical, (
        f"Expected {expected_critical} critical issues, got {critical}: "
        f"{[i for i in issues if 'CRITICAL' in i.upper()]}"
    )

    assert warnings == expected_warnings, (
        f"Expected {expected_warnings} warnings, got {warnings}: "
        f"{[i for i in issues if 'WARNING' in i.upper()]}"
    )

    return issues


def assert_no_critical_issues(settings: SettingsBase) -> None:
    """
    Assert settings have no critical validation issues.

    Args:
        settings: Settings to validate

    Raises:
        AssertionError: If critical issues found
    """
    issues = settings.validate(fail_fast=False)

    critical = [i for i in issues if "CRITICAL" in i.upper()]

    assert not critical, f"Critical issues found: {critical}"


class SettingsTestBuilder:
    """
    Fluent builder for test settings.

    Usage:
        settings = (
            SettingsTestBuilder(DatabaseSettings)
            .with_url("sqlite:///:memory:")
            .with_pool_size(10)
            .build()
        )
    """

    def __init__(self, settings_class: type[SettingsBase]):
        """Initialize builder with settings class."""
        self._settings_class = settings_class
        self._overrides: dict[str, Any] = {}

    def with_env(self, env: str) -> SettingsTestBuilder:
        """Set environment."""
        self._overrides["environment"] = env
        return self

    def with_url(self, url: str) -> SettingsTestBuilder:
        """Set database URL."""
        self._overrides["url"] = url
        return self

    def with_pool_size(self, size: int) -> SettingsTestBuilder:
        """Set pool size."""
        self._overrides["pool_size"] = size
        return self

    def with_secret_key(self, key: str) -> SettingsTestBuilder:
        """Set secret key."""
        self._overrides["secret_key"] = key
        return self

    def with_debug(self, debug: bool) -> SettingsTestBuilder:
        """Set debug mode."""
        self._overrides["debug"] = debug
        return self

    def with_overrides(self, **kwargs: Any) -> SettingsTestBuilder:
        """Add arbitrary overrides."""
        self._overrides.update(kwargs)
        return self

    def build(self) -> SettingsBase:
        """Build settings instance."""
        return self._settings_class.from_env(**self._overrides)

    def build_with_test_env(self) -> SettingsBase:
        """Build settings instance with test environment."""
        with test_settings_env():
            return self._settings_class.from_env(**self._overrides)


# Pytest fixtures (if pytest is available)
try:
    import pytest

    @pytest.fixture
    def test_env() -> Generator[dict[str, str]]:
        """Pytest fixture for test environment."""
        with test_settings_env() as env:
            yield env

    @pytest.fixture
    def prod_env() -> Generator[dict[str, str]]:
        """Pytest fixture for production environment."""
        with production_env() as env:
            yield env

except ImportError:
    # pytest not available, skip fixtures
    pass
