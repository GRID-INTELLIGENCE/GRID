"""
AI Safety and Security Utilities.

Implements best practices for AI API key management and validation
following industry guidelines and community standards.
"""

from __future__ import annotations

import logging
import os

from .secret_validation import get_secret_from_env, mask_secret

logger = logging.getLogger(__name__)


class AISafetyConfig:
    """
    AI Safety configuration following industry best practices.

    Ensures secure handling of AI API keys and prevents exposure
    of sensitive credentials in logs or error messages.
    """

    def __init__(self, environment: str = "production"):
        """
        Initialize AI safety configuration.

        Args:
            environment: Current environment (production, development, testing)
        """
        self.environment = environment.lower()
        self._api_keys: dict[str, str] = {}

    def get_gemini_api_key(self, required: bool = False) -> str | None:
        """
        Get Gemini API key from environment with validation.

        Args:
            required: Whether API key is required

        Returns:
            API key or None if not required and not set

        Raises:
            SecretValidationError: If required key is missing
        """
        key = get_secret_from_env(
            env_var="GEMINI_API_KEY",
            required=required and self.environment == "production",
            environment=self.environment,
            default=None,
        )

        if key:
            # Store masked for logging
            self._api_keys["gemini"] = mask_secret(key)
            logger.info(f"Gemini API key loaded (masked: {self._api_keys['gemini']})")

        return key

    def get_openai_api_key(self, required: bool = False) -> str | None:
        """
        Get OpenAI API key from environment with validation.

        Args:
            required: Whether API key is required

        Returns:
            API key or None if not required and not set

        Raises:
            SecretValidationError: If required key is missing
        """
        key = get_secret_from_env(
            env_var="OPENAI_API_KEY",
            required=required and self.environment == "production",
            environment=self.environment,
            default=None,
        )

        if key:
            self._api_keys["openai"] = mask_secret(key)
            logger.info(f"OpenAI API key loaded (masked: {self._api_keys['openai']})")

        return key

    def get_anthropic_api_key(self, required: bool = False) -> str | None:
        """
        Get Anthropic API key from environment with validation.

        Args:
            required: Whether API key is required

        Returns:
            API key or None if not required and not set

        Raises:
            SecretValidationError: If required key is missing
        """
        key = get_secret_from_env(
            env_var="ANTHROPIC_API_KEY",
            required=required and self.environment == "production",
            environment=self.environment,
            default=None,
        )

        if key:
            self._api_keys["anthropic"] = mask_secret(key)
            logger.info(f"Anthropic API key loaded (masked: {self._api_keys['anthropic']})")

        return key

    def validate_api_key_format(self, key: str, provider: str) -> bool:
        """
        Validate API key format for common providers.

        Args:
            key: API key to validate
            provider: Provider name (gemini, openai, anthropic)

        Returns:
            True if format appears valid, False otherwise
        """
        if not key or len(key) < 10:
            return False

        provider_lower = provider.lower()

        # Basic format validation (without exposing actual key patterns)
        if provider_lower == "gemini":
            # Gemini keys typically start with specific prefixes
            return len(key) >= 32
        elif provider_lower == "openai":
            # OpenAI keys start with "sk-"
            return key.startswith("sk-") and len(key) >= 32
        elif provider_lower == "anthropic":
            # Anthropic keys start with "sk-ant-"
            return key.startswith("sk-ant-") and len(key) >= 32

        # Unknown provider - just check minimum length
        return len(key) >= 32

    def sanitize_error_message(self, error: Exception, api_provider: str) -> str:
        """
        Sanitize error messages to prevent API key exposure.

        Args:
            error: Original error
            api_provider: API provider name

        Returns:
            Sanitized error message without sensitive information
        """
        error_msg = str(error)

        # Remove potential API key leaks from error messages
        sensitive_patterns = [
            "api_key",
            "apikey",
            "api-key",
            "secret",
            "token",
            "authorization",
            "auth",
        ]

        sanitized = error_msg
        for pattern in sensitive_patterns:
            # This is a basic sanitization - in production, use more sophisticated methods
            if pattern.lower() in error_msg.lower():
                logger.warning(f"Potential sensitive information in {api_provider} error message - sanitizing")
                # Don't expose the actual error details that might contain keys
                sanitized = f"API error from {api_provider} (details sanitized for security)"
                break

        return sanitized


# Global AI safety config instance
_ai_safety_config: AISafetyConfig | None = None


def get_ai_safety_config(environment: str | None = None) -> AISafetyConfig:
    """
    Get or create global AI safety configuration.

    Args:
        environment: Current environment (auto-detected if None)

    Returns:
        AISafetyConfig instance
    """
    global _ai_safety_config
    if _ai_safety_config is None:
        if environment is None:
            environment = os.getenv("MOTHERSHIP_ENVIRONMENT", "production")
        _ai_safety_config = AISafetyConfig(environment=environment)
    return _ai_safety_config


__all__ = [
    "AISafetyConfig",
    "get_ai_safety_config",
]
