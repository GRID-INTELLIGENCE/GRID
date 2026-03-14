"""Unit tests for infrastructure.config.base and factory modules."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from infrastructure.config.base import EnvironmentInfo, SettingsBase
from infrastructure.config.factory import (
    FactoryConfig,
    SettingsFactory,
    cached_settings,
    clear_all_caches,
    get_factory,
    get_registered_settings,
    register_factory,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class SampleSettings(SettingsBase):
    value: int = 1


class TestEnvironmentInfo:
    """Tests for EnvironmentInfo class."""

    def test_from_environment_development(self):
        """Test environment detection for development."""
        env = EnvironmentInfo.from_environment("development")
        assert env.environment == "development"
        assert env.is_development is True
        assert env.is_production is False

    def test_from_environment_production(self):
        """Test environment detection for production."""
        env = EnvironmentInfo.from_environment("production")
        assert env.environment == "production"
        assert env.is_development is False
        assert env.is_production is True

    def test_from_environment_test(self):
        """Test environment detection for test."""
        env = EnvironmentInfo.from_environment("test")
        assert env.environment == "test"
        assert env.is_test is True


class TestSettingsBase:
    """Tests for SettingsBase class."""

    def test_frozen_dataclass(self):
        """Test that settings are frozen (immutable)."""
        settings = SampleSettings(environment="development")
        with pytest.raises(Exception):  # frozen dataclass
            settings.environment = "production"

    def test_validate_method(self):
        """Test validate method can be overridden."""
        @dataclass(frozen=True, slots=True, kw_only=True)
        class ValidatedSettings(SettingsBase):
            valid: bool = False

            def validate(self, fail_fast: bool = False):
                if not self.valid:
                    raise ValueError("Must set valid")
                return []

        settings = ValidatedSettings(valid=True)
        settings.validate()  # Should not raise

    def test_to_dict(self):
        """Test to_dict method."""
        settings = SampleSettings(environment="development")
        result = settings.to_dict()
        assert result["environment"] == "development"

    def test_replace(self):
        """Test immutable updates with replace."""
        settings = SampleSettings(environment="development")
        new_settings = settings.replace(environment="production")
        assert new_settings.environment == "production"
        assert settings.environment == "development"  # Original unchanged


class TestSettingsFactory:
    """Tests for SettingsFactory class."""

    @pytest.fixture(autouse=True)
    def clear_caches(self):
        """Clear caches before each test."""
        clear_all_caches()
        yield
        clear_all_caches()

    def test_get_settings(self):
        """Test getting settings from factory."""
        factory = SettingsFactory(SampleSettings)
        settings = factory.get_settings("test")
        assert settings is not None
        assert isinstance(settings, SampleSettings)
        assert settings.environment == "test"

    def test_settings_caching(self):
        """Test settings are cached."""
        factory = SettingsFactory(SampleSettings)
        settings1 = factory.get_settings("test")
        settings2 = factory.get_settings("test")
        assert settings1 is settings2  # Same instance

    def test_different_environments(self):
        """Test different environments get different instances."""
        factory = SettingsFactory(SampleSettings)
        dev_settings = factory.get_settings("development")
        prod_settings = factory.get_settings("production")
        assert dev_settings is not prod_settings

    def test_register_and_get(self):
        """Test registering and retrieving settings."""
        clear_all_caches()

        register_factory("custom", SampleSettings)
        factory = get_factory("custom")
        assert factory is not None
        assert isinstance(factory, SettingsFactory)


class TestCachedSettings:
    """Tests for cached_settings decorator."""

    @pytest.fixture(autouse=True)
    def clear_caches(self):
        """Clear caches before each test."""
        clear_all_caches()
        yield
        clear_all_caches()

    def test_cached_decorator(self):
        """Test cached_settings decorator."""
        get_settings = cached_settings(SampleSettings)

        result1 = get_settings()
        result2 = get_settings()

        assert isinstance(result1, SampleSettings)
        assert result1 is result2

    def test_cached_with_environment(self):
        """Test cached settings with environment."""
        get_settings = cached_settings(SampleSettings)

        result1 = get_settings()
        result2 = get_settings()

        assert result1 is result2


class TestFactoryConfig:
    """Tests for FactoryConfig class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = FactoryConfig()
        assert config.env_prefix == ""
        assert config.cache_enabled is True
        assert config.cache_max_size == 16

    def test_custom_values(self):
        """Test custom configuration values."""
        config = FactoryConfig(
            env_prefix="APP_",
            cache_enabled=False,
            cache_max_size=8,
        )
        assert config.env_prefix == "APP_"
        assert config.cache_enabled is False
        assert config.cache_max_size == 8


class TestGetRegisteredSettings:
    """Tests for get_registered_settings function."""

    @pytest.fixture(autouse=True)
    def clear_caches(self):
        """Clear caches before each test."""
        clear_all_caches()
        yield
        clear_all_caches()

    def test_no_registrations(self):
        """Test no registrations returns empty."""
        settings = get_registered_settings("missing")
        assert settings is None

    def test_after_registration(self):
        """Test registration appears in list."""
        clear_all_caches()

        register_factory("test", SampleSettings)
        settings = get_registered_settings("test")
        assert isinstance(settings, SampleSettings)


class TestClearAllCaches:
    """Tests for clear_all_caches function."""

    def test_clear_clears_cache(self):
        """Test that clear_all_caches clears registered factory caches."""
        factory = register_factory("clear_test", SampleSettings)
        settings1 = factory.get_settings("test")

        clear_all_caches()

        settings2 = factory.get_settings("test")
        assert settings1 is not settings2
