"""Gemini Studio Cloud Configuration.

Configuration settings for Google Gemini Studio integration,
designed for seamless connectivity with cloud-hosted applications.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class GeminiModel(StrEnum):
    """Available Gemini model variants."""

    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"
    GEMINI_ULTRA = "gemini-ultra"
    GEMINI_FLASH = "gemini-1.5-flash"
    GEMINI_PRO_15 = "gemini-1.5-pro"


class DeploymentStage(StrEnum):
    """Deployment stages for cloud app lifecycle."""

    NOT_DEPLOYED = "not_deployed"
    STAGING = "staging"
    PREVIEW = "preview"
    PRODUCTION = "production"


def _parse_bool(value: str | None) -> bool:
    """Parse a boolean-ish environment variable."""
    if value is None:
        return False
    value_norm = value.strip().lower()
    return value_norm in {"true", "1", "yes", "y"}


@dataclass
class GeminiAuthSettings:
    """Authentication configuration for Gemini Studio."""

    api_key: str = ""
    project_id: str = ""
    service_account_path: str | None = None
    use_adc: bool = True  # Application Default Credentials
    oauth_client_id: str | None = None
    oauth_client_secret: str | None = None

    @classmethod
    def from_env(cls) -> GeminiAuthSettings:
        """Load authentication settings from environment variables."""
        env = os.environ
        return cls(
            api_key=env.get("GEMINI_API_KEY", ""),
            project_id=env.get("GOOGLE_CLOUD_PROJECT", env.get("GCP_PROJECT_ID", "")),
            service_account_path=env.get("GOOGLE_APPLICATION_CREDENTIALS"),
            use_adc=_parse_bool(env.get("GEMINI_USE_ADC", "true")),
            oauth_client_id=env.get("GEMINI_OAUTH_CLIENT_ID"),
            oauth_client_secret=env.get("GEMINI_OAUTH_CLIENT_SECRET"),
        )

    @property
    def is_configured(self) -> bool:
        """Check if authentication is properly configured."""
        return bool(self.api_key or (self.use_adc and self.project_id))


@dataclass
class GeminiEndpointSettings:
    """Endpoint configuration for Gemini Studio cloud app."""

    base_url: str = "https://generativelanguage.googleapis.com"
    api_version: str = "v1beta"
    studio_url: str = "https://aistudio.google.com"
    region: str = "us-central1"
    custom_endpoint: str | None = None

    @classmethod
    def from_env(cls) -> GeminiEndpointSettings:
        """Load endpoint settings from environment variables."""
        env = os.environ
        return cls(
            base_url=env.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com"),
            api_version=env.get("GEMINI_API_VERSION", "v1beta"),
            studio_url=env.get("GEMINI_STUDIO_URL", "https://aistudio.google.com"),
            region=env.get("GEMINI_REGION", "us-central1"),
            custom_endpoint=env.get("GEMINI_CUSTOM_ENDPOINT"),
        )

    @property
    def effective_url(self) -> str:
        """Return the effective API URL to use."""
        if self.custom_endpoint:
            return self.custom_endpoint
        return f"{self.base_url}/{self.api_version}"


@dataclass
class GeminiModelSettings:
    """Model configuration for Gemini inference."""

    default_model: str = GeminiModel.GEMINI_PRO_15.value
    temperature: float = 0.7
    max_output_tokens: int = 2048
    top_p: float = 0.95
    top_k: int = 40
    stop_sequences: list = field(default_factory=list)
    safety_settings: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> GeminiModelSettings:
        """Load model settings from environment variables."""
        env = os.environ
        return cls(
            default_model=env.get("GEMINI_MODEL", GeminiModel.GEMINI_PRO_15.value),
            temperature=float(env.get("GEMINI_TEMPERATURE", "0.7")),
            max_output_tokens=int(env.get("GEMINI_MAX_TOKENS", "2048")),
            top_p=float(env.get("GEMINI_TOP_P", "0.95")),
            top_k=int(env.get("GEMINI_TOP_K", "40")),
        )


@dataclass
class GeminiRateLimitSettings:
    """Rate limiting and retry configuration."""

    requests_per_minute: int = 60
    tokens_per_minute: int = 60000
    max_retries: int = 3
    retry_delay_base: float = 1.0
    retry_delay_max: float = 60.0
    timeout_seconds: int = 120

    @classmethod
    def from_env(cls) -> GeminiRateLimitSettings:
        """Load rate limit settings from environment variables."""
        env = os.environ
        return cls(
            requests_per_minute=int(env.get("GEMINI_RPM", "60")),
            tokens_per_minute=int(env.get("GEMINI_TPM", "60000")),
            max_retries=int(env.get("GEMINI_MAX_RETRIES", "3")),
            retry_delay_base=float(env.get("GEMINI_RETRY_DELAY", "1.0")),
            timeout_seconds=int(env.get("GEMINI_TIMEOUT", "120")),
        )


@dataclass
class GeminiSettings:
    """Top-level Gemini Studio cloud configuration.

    Centralizes all settings for connecting to a Gemini Studio
    hosted application (pre-deployment or deployed).
    """

    enabled: bool = True
    deployment_stage: DeploymentStage = DeploymentStage.NOT_DEPLOYED
    app_name: str = "grid-gemini-integration"

    auth: GeminiAuthSettings = field(default_factory=GeminiAuthSettings.from_env)
    endpoint: GeminiEndpointSettings = field(default_factory=GeminiEndpointSettings.from_env)
    model: GeminiModelSettings = field(default_factory=GeminiModelSettings.from_env)
    rate_limit: GeminiRateLimitSettings = field(default_factory=GeminiRateLimitSettings.from_env)

    # Feature flags for pre-deployment testing
    mock_responses: bool = False
    enable_streaming: bool = True
    enable_function_calling: bool = True
    enable_code_execution: bool = False
    verbose_logging: bool = False

    @classmethod
    def from_env(cls) -> GeminiSettings:
        """Load all Gemini settings from environment variables."""
        env = os.environ
        stage_str = env.get("GEMINI_DEPLOYMENT_STAGE", "not_deployed")
        try:
            stage = DeploymentStage(stage_str)
        except ValueError:
            stage = DeploymentStage.NOT_DEPLOYED

        return cls(
            enabled=_parse_bool(env.get("GEMINI_ENABLED", "true")),
            deployment_stage=stage,
            app_name=env.get("GEMINI_APP_NAME", "grid-gemini-integration"),
            mock_responses=_parse_bool(env.get("GEMINI_MOCK_RESPONSES", "")),
            enable_streaming=_parse_bool(env.get("GEMINI_STREAMING", "true")),
            enable_function_calling=_parse_bool(env.get("GEMINI_FUNCTION_CALLING", "true")),
            enable_code_execution=_parse_bool(env.get("GEMINI_CODE_EXECUTION", "")),
            verbose_logging=_parse_bool(env.get("GEMINI_VERBOSE", "")),
        )

    @property
    def is_ready(self) -> bool:
        """Check if the integration is ready for use."""
        if not self.enabled:
            return False
        if self.mock_responses:
            return True  # Mock mode doesn't need real credentials
        return self.auth.is_configured

    @property
    def is_deployed(self) -> bool:
        """Check if the cloud app is deployed."""
        return self.deployment_stage != DeploymentStage.NOT_DEPLOYED

    def to_dict(self) -> dict[str, Any]:
        """Export settings as dictionary (masks sensitive values)."""
        return {
            "enabled": self.enabled,
            "deployment_stage": self.deployment_stage.value,
            "app_name": self.app_name,
            "is_ready": self.is_ready,
            "is_deployed": self.is_deployed,
            "auth": {
                "has_api_key": bool(self.auth.api_key),
                "project_id": self.auth.project_id or "(not set)",
                "use_adc": self.auth.use_adc,
            },
            "endpoint": {
                "base_url": self.endpoint.base_url,
                "api_version": self.endpoint.api_version,
                "region": self.endpoint.region,
            },
            "model": {
                "default_model": self.model.default_model,
                "temperature": self.model.temperature,
                "max_output_tokens": self.model.max_output_tokens,
            },
            "features": {
                "mock_responses": self.mock_responses,
                "streaming": self.enable_streaming,
                "function_calling": self.enable_function_calling,
                "code_execution": self.enable_code_execution,
            },
        }


# Module-level singleton
_gemini_settings: GeminiSettings | None = None


def get_gemini_settings(reload: bool = False) -> GeminiSettings:
    """Return cached Gemini settings instance."""
    global _gemini_settings
    if _gemini_settings is None or reload:
        _gemini_settings = GeminiSettings.from_env()
    return _gemini_settings


# Initialize on import
gemini_settings = get_gemini_settings()


__all__ = [
    "GeminiSettings",
    "GeminiAuthSettings",
    "GeminiEndpointSettings",
    "GeminiModelSettings",
    "GeminiRateLimitSettings",
    "GeminiModel",
    "DeploymentStage",
    "get_gemini_settings",
    "gemini_settings",
]
