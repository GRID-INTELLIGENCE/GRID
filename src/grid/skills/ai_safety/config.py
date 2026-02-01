"""AI Safety Skills Configuration.

Manages configuration for AI safety skills including provider endpoints,
thresholds, and feature flags.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

from .base import ThreatLevel

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    """Configuration for a single AI provider."""

    name: str
    api_key_env: str
    api_endpoint: str | None = None
    enabled: bool = True
    timeout_seconds: int = 30
    rate_limit_per_minute: int = 60


@dataclass
class AISafetyConfig:
    """Configuration for AI safety skills.

    Loads from environment variables following the pattern from
    application/mothership/security/ai_safety.py.
    """

    # Feature flags
    enable_content_moderation: bool = True
    enable_behavior_analysis: bool = True
    enable_threat_detection: bool = True
    enable_provider_failover: bool = True

    # Safety thresholds
    safety_thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "safe": 0.8,
            "warning": 0.6,
            "danger": 0.4,
        }
    )

    # Default severity threshold for actions
    default_severity_threshold: ThreatLevel = ThreatLevel.MEDIUM

    # Provider configurations
    providers: dict[str, ProviderConfig] = field(
        default_factory=lambda: {
            "openai": ProviderConfig(
                name="openai",
                api_key_env="OPENAI_API_KEY",
                api_endpoint="https://api.openai.com/v1/moderations",
            ),
            "anthropic": ProviderConfig(
                name="anthropic",
                api_key_env="ANTHROPIC_API_KEY",
                api_endpoint="https://api.anthropic.com/v1/messages",
            ),
            "google": ProviderConfig(
                name="google",
                api_key_env="GEMINI_API_KEY",
                api_endpoint="https://generativelanguage.googleapis.com/v1beta",
            ),
            "xai": ProviderConfig(
                name="xai",
                api_key_env="XAI_API_KEY",
                api_endpoint="https://api.x.ai/v1",
            ),
            "mistral": ProviderConfig(
                name="mistral",
                api_key_env="MISTRAL_API_KEY",
                api_endpoint="https://api.mistral.ai/v1",
            ),
            "nvidia": ProviderConfig(
                name="nvidia",
                api_key_env="NVIDIA_API_KEY",
                api_endpoint="https://api.nvidia.com/v1",
            ),
            "llama": ProviderConfig(
                name="llama",
                api_key_env="LLAMA_API_KEY",
                api_endpoint=None,  # Local inference by default
            ),
        }
    )

    # Monitoring settings
    monitoring_enabled: bool = True
    monitoring_check_interval_seconds: int = 60
    max_violations_per_hour: int = 100

    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300

    @classmethod
    def from_env(cls) -> AISafetyConfig:
        """Load configuration from environment variables.

        Returns:
            AISafetyConfig instance with values from environment.
        """
        config = cls()

        # Load feature flags
        config.enable_content_moderation = os.getenv("AI_SAFETY_ENABLE_CONTENT_MODERATION", "true").lower() == "true"
        config.enable_behavior_analysis = os.getenv("AI_SAFETY_ENABLE_BEHAVIOR_ANALYSIS", "true").lower() == "true"
        config.enable_threat_detection = os.getenv("AI_SAFETY_ENABLE_THREAT_DETECTION", "true").lower() == "true"
        config.enable_provider_failover = os.getenv("AI_SAFETY_ENABLE_PROVIDER_FAILOVER", "true").lower() == "true"

        # Load thresholds
        safe_threshold = os.getenv("AI_SAFETY_THRESHOLD_SAFE")
        if safe_threshold:
            config.safety_thresholds["safe"] = float(safe_threshold)

        warning_threshold = os.getenv("AI_SAFETY_THRESHOLD_WARNING")
        if warning_threshold:
            config.safety_thresholds["warning"] = float(warning_threshold)

        danger_threshold = os.getenv("AI_SAFETY_THRESHOLD_DANGER")
        if danger_threshold:
            config.safety_thresholds["danger"] = float(danger_threshold)

        # Load monitoring settings
        monitoring_enabled = os.getenv("AI_SAFETY_MONITORING_ENABLED")
        if monitoring_enabled:
            config.monitoring_enabled = monitoring_enabled.lower() == "true"

        check_interval = os.getenv("AI_SAFETY_MONITORING_INTERVAL")
        if check_interval:
            config.monitoring_check_interval_seconds = int(check_interval)

        # Update provider configurations from environment
        for provider_name, provider_config in config.providers.items():
            enabled_env = os.getenv(f"AI_SAFETY_{provider_name.upper()}_ENABLED")
            if enabled_env:
                provider_config.enabled = enabled_env.lower() == "true"

            timeout_env = os.getenv(f"AI_SAFETY_{provider_name.upper()}_TIMEOUT")
            if timeout_env:
                provider_config.timeout_seconds = int(timeout_env)

            rate_limit_env = os.getenv(f"AI_SAFETY_{provider_name.upper()}_RATE_LIMIT")
            if rate_limit_env:
                provider_config.rate_limit_per_minute = int(rate_limit_env)

        logger.info("AI Safety configuration loaded from environment")
        return config

    def get_provider_api_key(self, provider_name: str) -> str | None:
        """Get API key for a provider.

        Args:
            provider_name: Name of the provider.

        Returns:
            API key or None if not set.
        """
        provider_config = self.providers.get(provider_name)
        if not provider_config:
            return None

        api_key = os.getenv(provider_config.api_key_env)
        if api_key:
            logger.debug(f"API key loaded for {provider_name}")
        return api_key

    def is_provider_enabled(self, provider_name: str) -> bool:
        """Check if a provider is enabled.

        Args:
            provider_name: Name of the provider.

        Returns:
            True if enabled and has API key.
        """
        provider_config = self.providers.get(provider_name)
        if not provider_config:
            return False

        if not provider_config.enabled:
            return False

        # Check if API key is available
        api_key = self.get_provider_api_key(provider_name)
        return api_key is not None and len(api_key) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation (API keys masked).
        """
        return {
            "enable_content_moderation": self.enable_content_moderation,
            "enable_behavior_analysis": self.enable_behavior_analysis,
            "enable_threat_detection": self.enable_threat_detection,
            "enable_provider_failover": self.enable_provider_failover,
            "safety_thresholds": self.safety_thresholds,
            "default_severity_threshold": self.default_severity_threshold.value,
            "providers": {
                name: {
                    "name": cfg.name,
                    "enabled": cfg.enabled,
                    "timeout_seconds": cfg.timeout_seconds,
                    "rate_limit_per_minute": cfg.rate_limit_per_minute,
                    "has_api_key": self.get_provider_api_key(name) is not None,
                }
                for name, cfg in self.providers.items()
            },
            "monitoring_enabled": self.monitoring_enabled,
            "monitoring_check_interval_seconds": self.monitoring_check_interval_seconds,
            "max_violations_per_hour": self.max_violations_per_hour,
            "cache_enabled": self.cache_enabled,
            "cache_ttl_seconds": self.cache_ttl_seconds,
        }


# Global configuration instance
_config: AISafetyConfig | None = None


def get_config() -> AISafetyConfig:
    """Get the global AI safety configuration.

    Returns:
        AISafetyConfig instance (singleton).
    """
    global _config
    if _config is None:
        _config = AISafetyConfig.from_env()
    return _config


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None
