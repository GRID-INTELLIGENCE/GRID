"""Tests for AI Safety Configuration."""

from grid.skills.ai_safety.config import AISafetyConfig, ProviderConfig, get_config, reset_config


class TestProviderConfig:
    """Test provider configuration."""

    def test_provider_config_creation(self):
        """Test creating provider config."""
        config = ProviderConfig(
            name="test_provider",
            api_key_env="TEST_API_KEY",
            api_endpoint="https://test.example.com",
        )
        assert config.name == "test_provider"
        assert config.api_key_env == "TEST_API_KEY"
        assert config.enabled is True


class TestAISafetyConfig:
    """Test AI safety configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AISafetyConfig()
        assert config.enable_content_moderation is True
        assert config.enable_behavior_analysis is True
        assert config.enable_threat_detection is True
        assert "safe" in config.safety_thresholds
        assert config.safety_thresholds["safe"] == 0.8

    def test_load_from_env(self):
        """Test loading config from environment."""
        config = AISafetyConfig.from_env()
        assert isinstance(config, AISafetyConfig)
        assert len(config.providers) == 7

    def test_get_provider_api_key_not_set(self, monkeypatch):
        """Test getting API key when not set."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        config = AISafetyConfig()
        key = config.get_provider_api_key("openai")
        assert key is None

    def test_is_provider_enabled_no_key(self, monkeypatch):
        """Test provider disabled when no API key."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        config = AISafetyConfig()
        # Provider is enabled in config but no API key set
        assert config.is_provider_enabled("openai") is False

    def test_to_dict_masks_api_keys(self):
        """Test that to_dict masks API keys."""
        config = AISafetyConfig()
        data = config.to_dict()
        assert "providers" in data
        # Should not contain actual API keys
        for provider_data in data["providers"].values():
            assert "has_api_key" in provider_data

    def test_safety_thresholds(self):
        """Test safety threshold configuration."""
        config = AISafetyConfig()
        assert config.safety_thresholds["safe"] == 0.8
        assert config.safety_thresholds["warning"] == 0.6
        assert config.safety_thresholds["danger"] == 0.4


class TestGlobalConfig:
    """Test global configuration functions."""

    def test_get_config_singleton(self):
        """Test that get_config returns singleton."""
        reset_config()
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config(self):
        """Test resetting global config."""
        reset_config()
        config1 = get_config()
        reset_config()
        config2 = get_config()
        assert config1 is not config2
