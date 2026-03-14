"""
Settings Factory Pattern.

Replaces singleton anti-pattern with factory + caching:
- Testable: Easy to mock/override
- Explicit: Dependencies are clear
- Flexible: Multiple configurations possible

Based on research showing singleton is an anti-pattern in modern Python.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .base import SettingsBase

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FactoryConfig:
    """Configuration for settings factory."""

    env_prefix: str = ""
    cache_enabled: bool = True
    cache_max_size: int = 16


class SettingsFactory:
    """
    Factory for creating and caching settings instances.

    Replaces singleton pattern with explicit dependency injection:
    - Cache is opt-in, not forced
    - Easy to create fresh instances for testing
    - Multiple configurations can coexist

    Usage:
        # Basic usage with caching
        factory = SettingsFactory(DatabaseSettings)
        settings = factory.get_settings()

        # Override for testing
        test_settings = factory.create(fresh=True, url="sqlite:///:memory:")

        # Multiple environments
        dev_settings = factory.get_settings(env="development")
        prod_settings = factory.get_settings(env="production")

        # Clear cache
        factory.clear_cache()
    """

    def __init__(
        self,
        settings_class: type[SettingsBase],
        *,
        config: FactoryConfig | None = None,
    ):
        """
        Initialize factory.

        Args:
            settings_class: Settings class to create instances of
            config: Optional factory configuration
        """
        self._settings_class = settings_class
        self._config = config or FactoryConfig()
        self._cache: dict[str, SettingsBase] = {}

    def get_settings(
        self,
        env: str | None = None,
        **overrides: Any,
    ) -> SettingsBase:
        """
        Get settings instance (cached by default).

        Args:
            env: Optional environment name for cache key
            **overrides: Field overrides

        Returns:
            Settings instance (cached if cache_enabled)
        """
        if not self._config.cache_enabled:
            return self.create(env=env, **overrides)

        cache_key = self._make_cache_key(env, overrides)

        if cache_key not in self._cache:
            self._cache[cache_key] = self.create(env=env, **overrides)
            logger.debug(f"Created and cached settings: {cache_key}")

        return self._cache[cache_key]

    def create(
        self,
        env: str | None = None,
        fresh: bool = False,
        **overrides: Any,
    ) -> SettingsBase:
        """
        Create a new settings instance.

        Args:
            env: Optional environment name
            fresh: If True, bypass cache
            **overrides: Field overrides

        Returns:
            Fresh settings instance
        """
        # Merge env into overrides
        if env:
            overrides["environment"] = env

        # Create instance via from_env
        settings = self._settings_class.from_env(
            prefix=self._config.env_prefix,
            **overrides,
        )

        return settings

    def _make_cache_key(self, env: str | None, overrides: dict[str, Any]) -> str:
        """Generate cache key from env and overrides."""
        parts = [env or "default"]

        # Sort overrides for consistent keys
        for key, value in sorted(overrides.items()):
            parts.append(f"{key}={value}")

        return "|".join(parts)

    def clear_cache(self) -> None:
        """Clear all cached settings."""
        self._cache.clear()
        logger.debug("Settings cache cleared")

    def cached_keys(self) -> list[str]:
        """Get list of cached keys (for debugging)."""
        return list(self._cache.keys())


# Module-level factory registry
_factories: dict[str, SettingsFactory] = {}


def register_factory(
    name: str,
    settings_class: type[SettingsBase],
    *,
    config: FactoryConfig | None = None,
) -> SettingsFactory:
    """
    Register a named factory.

    Args:
        name: Factory name for later retrieval
        settings_class: Settings class
        config: Optional factory config

    Returns:
        Created factory instance
    """
    factory = SettingsFactory(settings_class, config=config)
    _factories[name] = factory
    return factory


def get_factory(name: str) -> SettingsFactory | None:
    """Get registered factory by name."""
    return _factories.get(name)


def get_registered_settings(name: str, env: str | None = None) -> SettingsBase | None:
    """
    Get settings from a registered factory.

    Args:
        name: Factory name
        env: Optional environment

    Returns:
        Settings instance or None if factory not found
    """
    factory = _factories.get(name)
    if factory:
        return factory.get_settings(env=env)
    return None


def clear_all_caches() -> None:
    """Clear all factory caches."""
    for factory in _factories.values():
        factory.clear_cache()
    logger.debug("All settings caches cleared")


# Decorator for creating cached settings getter
def cached_settings(
    settings_class: type[SettingsBase],
    *,
    env_prefix: str = "",
) -> Callable[[], SettingsBase]:
    """
    Decorator to create a cached settings getter function.

    Usage:
        @cached_settings(DatabaseSettings, env_prefix="DB_")
        def get_db_settings() -> DatabaseSettings:
            ...

        # Or as a simple factory:
        get_settings = cached_settings(AppSettings)
        settings = get_settings()
    """
    factory = SettingsFactory(
        settings_class,
        config=FactoryConfig(env_prefix=env_prefix),
    )

    @lru_cache(maxsize=1)
    def getter() -> SettingsBase:
        return factory.get_settings()

    return getter
