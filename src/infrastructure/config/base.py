"""
Modern Settings Base Class with 2026 Best Practices.

Features:
- @dataclass(frozen=True, slots=True, kw_only=True) for thread safety and memory efficiency
- Immutable by default - use replace() for updates
- Environment-aware validation with fail_fast pattern
- Composable via inheritance

Based on patterns extracted from Mothership configuration system.
"""

from __future__ import annotations

import dataclasses
import logging
import os
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class SettingsBase:
    """
    Modern configuration base following 2026 best practices.

    Features:
    - frozen=True: Immutable, thread-safe, hashable
    - slots=True: ~30-40% memory reduction
    - kw_only=True: Prevents positional argument confusion

    Usage:
        @dataclass(frozen=True, slots=True, kw_only=True)
        class DatabaseSettings(SettingsBase):
            url: str = "sqlite:///./app.db"
            pool_size: int = 5

            @classmethod
            def from_env(cls, prefix: str = "DB_") -> "DatabaseSettings":
                return cls(
                    url=os.getenv(f"{prefix}URL", "sqlite:///./app.db"),
                    pool_size=int(os.getenv(f"{prefix}POOL_SIZE", "5")),
                )

            def validate(self, fail_fast: bool = False) -> list[str]:
                issues = []
                if not self.url:
                    issues.append("Database URL is required")
                return issues
    """

    # Class-level registry for settings instances (used by factory)
    _registry: ClassVar[dict[str, SettingsBase]] = {}

    # Environment metadata (optional, for context-aware validation)
    environment: str = field(default="development", repr=False)
    is_production: bool = field(default=False, compare=False)

    @classmethod
    def from_env(cls, prefix: str = "", **overrides: Any) -> SettingsBase:
        """
        Factory method to create from environment variables.

        Override in subclasses to implement specific loading logic.

        Args:
            prefix: Environment variable prefix (e.g., "MOTHERSHIP_")
            **overrides: Override specific fields

        Returns:
            Configured settings instance
        """
        env = os.environ
        env_override = overrides.pop("environment", None)
        env_str = (env_override or env.get(f"{prefix}ENVIRONMENT", "development")).lower()

        return cls(
            environment=env_str,
            is_production=env_str == "production",
            **overrides,
        )

    def validate(self, fail_fast: bool = False) -> list[str]:
        """
        Validate settings and return list of issues.

        Override in subclasses for domain-specific validation.

        Args:
            fail_fast: If True, raise ValueError on first issue

        Returns:
            List of validation issue strings

        Raises:
            ValueError: If fail_fast=True and issues found
        """
        issues: list[str] = []
        # Subclasses implement validation logic
        if issues and fail_fast:
            raise ValueError(f"Configuration errors: {issues}")
        return issues

    def replace(self, **changes: Any) -> SettingsBase:
        """
        Create a new instance with updated fields.

        Uses dataclasses.replace() for immutable updates.

        Args:
            **changes: Fields to update

        Returns:
            New settings instance with updated fields
        """
        return replace(self, **changes)

    def to_dict(self, mask_secrets: bool = True) -> dict[str, Any]:
        """
        Export to dictionary for serialization/logging.

        Args:
            mask_secrets: If True, mask sensitive fields

        Returns:
            Dictionary representation
        """
        result = dataclasses.asdict(self)

        if mask_secrets:
            result = self._mask_secrets(result)

        return result

    def _mask_secrets(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Mask sensitive fields in dictionary.

        Override in subclasses to specify which fields to mask.
        """
        secret_patterns = {"secret", "key", "token", "password", "credential"}

        def mask_value(key: str, value: Any) -> Any:
            if not isinstance(value, str) or not value:
                return value

            key_lower = key.lower()
            if any(pattern in key_lower for pattern in secret_patterns):
                if len(value) > 8:
                    return f"{value[:4]}***{value[-4:]}"
                return "***"
            return value

        return {k: mask_value(k, v) for k, v in data.items()}

    @classmethod
    def register(cls, name: str, instance: SettingsBase) -> None:
        """Register a settings instance in the class registry."""
        cls._registry[name] = instance

    @classmethod
    def get_registered(cls, name: str) -> SettingsBase | None:
        """Get a registered settings instance by name."""
        return cls._registry.get(name)


@dataclass(frozen=True, slots=True, kw_only=True)
class EnvironmentInfo:
    """
    Environment metadata extracted from settings.

    Provides convenient access to environment-aware behavior.
    """

    name: str = "development"
    is_production: bool = False
    is_development: bool = True
    is_testing: bool = False
    is_staging: bool = False

    @property
    def environment(self) -> str:
        """Backward-compatible alias for environment name."""
        return self.name

    @property
    def is_test(self) -> bool:
        """Backward-compatible alias for test environment flag."""
        return self.is_testing

    @classmethod
    def from_string(cls, env_str: str) -> EnvironmentInfo:
        """Create from environment string."""
        env_lower = env_str.lower()
        return cls(
            name=env_lower,
            is_production=env_lower == "production",
            is_development=env_lower in ("development", "dev", "local"),
            is_testing=env_lower in ("testing", "test"),
            is_staging=env_lower in ("staging", "stage"),
        )

    @classmethod
    def from_env(cls, var_name: str = "ENVIRONMENT") -> EnvironmentInfo:
        """Create from environment variable."""
        env_str = os.getenv(var_name, "development")
        return cls.from_string(env_str)

    @classmethod
    def from_environment(cls, env_str: str) -> EnvironmentInfo:
        """Backward-compatible constructor from explicit environment string."""
        return cls.from_string(env_str)
