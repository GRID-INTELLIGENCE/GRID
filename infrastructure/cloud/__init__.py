"""Gemini Studio Cloud Integration Module.

Provides seamless integration with Google AI Studio (Gemini) cloud-hosted
applications. Supports authentication, API calls, and configuration
management for pre-deployment and production environments.

Usage:
    from infra.cloud import GeminiCloudClient, GeminiConfig

    client = GeminiCloudClient.from_env()
    response = await client.invoke("your-model-endpoint", payload)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from types import TracebackType
from typing import Any, TypeVar
from urllib.parse import urljoin

try:
    import aiohttp  # type: ignore[import-not-found]

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


logger = logging.getLogger(__name__)

T = TypeVar("T")


class GeminiEnvironment(str, Enum):
    """Gemini Studio deployment environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"  # For pre-deployment testing


class AuthMethod(str, Enum):
    """Supported authentication methods."""

    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    SERVICE_ACCOUNT = "service_account"


@dataclass
class GeminiConfig:
    """Configuration for Gemini Studio cloud integration.

    Attributes:
        project_id: Google Cloud project ID
        api_key: Gemini API key (if using API key auth)
        region: Cloud region for the deployment
        environment: Target environment
        base_url: Base URL for Gemini Studio API
        timeout_seconds: Request timeout
        max_retries: Maximum retry attempts
        auth_method: Authentication method to use
        service_account_path: Path to service account JSON
        model_name: Default model name to use
    """

    project_id: str = ""
    api_key: str = ""
    region: str = "us-central1"
    environment: GeminiEnvironment = GeminiEnvironment.DEVELOPMENT
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    timeout_seconds: int = 60
    max_retries: int = 3
    auth_method: AuthMethod = AuthMethod.API_KEY
    service_account_path: str | None = None
    model_name: str = "gemini-1.5-flash"
    enable_streaming: bool = True
    rate_limit_rpm: int = 60

    # Pre-deployment configuration
    studio_project_url: str | None = None
    studio_email: str = "caraxesthebloodwyrm02@gmail.com"  # Default studio integration email
    pending_deployment: bool = True
    mock_responses: bool = False

    @classmethod
    def from_env(cls) -> GeminiConfig:
        """Load configuration from environment variables."""
        env = os.environ

        environment_str = env.get("GEMINI_ENVIRONMENT", "development").lower()
        try:
            environment = GeminiEnvironment(environment_str)
        except ValueError:
            environment = GeminiEnvironment.DEVELOPMENT

        auth_method_str = env.get("GEMINI_AUTH_METHOD", "api_key").lower()
        try:
            auth_method = AuthMethod(auth_method_str)
        except ValueError:
            auth_method = AuthMethod.API_KEY

        return cls(
            project_id=env.get("GEMINI_PROJECT_ID", env.get("GOOGLE_CLOUD_PROJECT", "")),
            api_key=env.get("GEMINI_API_KEY", env.get("GOOGLE_API_KEY", "")),
            region=env.get("GEMINI_REGION", "us-central1"),
            environment=environment,
            base_url=env.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
            timeout_seconds=int(env.get("GEMINI_TIMEOUT", "60")),
            max_retries=int(env.get("GEMINI_MAX_RETRIES", "3")),
            auth_method=auth_method,
            service_account_path=env.get("GOOGLE_APPLICATION_CREDENTIALS"),
            model_name=env.get("GEMINI_MODEL", "gemini-1.5-flash"),
            enable_streaming=env.get("GEMINI_STREAMING", "true").lower() == "true",
            rate_limit_rpm=int(env.get("GEMINI_RATE_LIMIT", "60")),
            studio_project_url=env.get("GEMINI_STUDIO_URL"),
            pending_deployment=env.get("GEMINI_DEPLOYED", "false").lower() != "true",
            mock_responses=env.get("GEMINI_MOCK", "false").lower() == "true",
        )

    def validate(self) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []

        if self.auth_method == AuthMethod.API_KEY and not self.api_key:
            issues.append("API key required when using API_KEY auth method")

        if self.auth_method == AuthMethod.SERVICE_ACCOUNT:
            if not self.service_account_path:
                issues.append("Service account path required for SERVICE_ACCOUNT auth")
            elif not os.path.exists(self.service_account_path):
                issues.append(f"Service account file not found: {self.service_account_path}")

        if self.timeout_seconds < 1:
            issues.append("Timeout must be at least 1 second")

        return issues


@dataclass
class GeminiResponse:
    """Standardized response from Gemini API."""

    success: bool
    data: dict[str, Any] | None = None
    text: str | None = None
    error: str | None = None
    status_code: int = 0
    latency_ms: float = 0.0
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_api_response(cls, response_data: dict[str, Any], latency: float = 0.0) -> GeminiResponse:
        """Parse API response into standardized format."""
        try:
            candidates = response_data.get("candidates", [])
            text = ""
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    text = parts[0].get("text", "")

            usage_metadata = response_data.get("usageMetadata", {})

            return cls(
                success=True,
                data=response_data,
                text=text,
                status_code=200,
                latency_ms=latency,
                model=response_data.get("modelVersion", ""),
                usage={
                    "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
                    "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
                    "total_tokens": usage_metadata.get("totalTokenCount", 0),
                },
            )
        except Exception as e:
            return cls(
                success=False,
                error=f"Failed to parse response: {e}",
                data=response_data,
            )

    @classmethod
    def error_response(cls, error: str, status_code: int = 500) -> GeminiResponse:
        """Create an error response."""
        return cls(success=False, error=error, status_code=status_code)

    @classmethod
    def mock_response(cls, prompt: str) -> GeminiResponse:
        """Create a mock response for pre-deployment testing."""
        return cls(
            success=True,
            text=f"[MOCK] Response for: {prompt[:50]}...",
            status_code=200,
            model="mock-gemini",
            usage={
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": 10,
                "total_tokens": len(prompt.split()) + 10,
            },
        )


class GeminiAuthenticator:
    """Handles authentication for Gemini Studio API."""

    def __init__(self, config: GeminiConfig):
        self.config = config
        self._token: str | None = None
        self._token_expiry: float = 0

    async def get_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests."""
        headers = {
            "Content-Type": "application/json",
        }

        if self.config.auth_method == AuthMethod.API_KEY:
            # API key is passed as query param, not header
            pass
        elif self.config.auth_method == AuthMethod.OAUTH2:
            token = await self._get_oauth_token()
            headers["Authorization"] = f"Bearer {token}"
        elif self.config.auth_method == AuthMethod.SERVICE_ACCOUNT:
            token = await self._get_service_account_token()
            headers["Authorization"] = f"Bearer {token}"

        return headers

    def get_query_params(self) -> dict[str, str]:
        """Get query parameters including API key if applicable."""
        params = {}
        if self.config.auth_method == AuthMethod.API_KEY and self.config.api_key:
            params["key"] = self.config.api_key
        return params

    async def _get_oauth_token(self) -> str:
        """Get OAuth2 token using google-auth (ADC or default credentials)."""
        try:
            import google.auth
            from google.auth.transport.requests import Request

            def _fetch() -> str:
                credentials, _ = google.auth.default(
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                if credentials.expired:
                    credentials.refresh(Request())
                return credentials.token or ""

            return await asyncio.to_thread(_fetch) or self._token or ""
        except ImportError:
            logger.warning("google-auth not installed. Install with: pip install google-auth")
            return self._token or ""
        except Exception as e:
            logger.warning("OAuth2 token refresh failed: %s", e)
            return self._token or ""

    async def _get_service_account_token(self) -> str:
        """Get service account token using google-auth."""
        try:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request

            path = self.config.service_account_path or os.environ.get(
                "GOOGLE_APPLICATION_CREDENTIALS"
            )
            if path and os.path.isfile(path):
                credentials = service_account.Credentials.from_service_account_file(
                    path, scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                credentials.refresh(Request())
                return credentials.token or ""
            import google.auth

            def _adc_token() -> str:
                creds, _ = google.auth.default(
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                if creds.expired:
                    creds.refresh(Request())
                return creds.token or ""

            return await asyncio.to_thread(_adc_token) or self._token or ""
        except ImportError:
            logger.warning("google-auth not installed. Install with: pip install google-auth")
            return self._token or ""
        except Exception as e:
            logger.warning("Service account token refresh failed: %s", e)
            return self._token or ""


class GeminiCloudClient:
    """Client for interacting with Gemini Studio cloud applications.

    Supports both deployed and pre-deployment (mock) modes for seamless
    development workflow with Gemini Studio.

    Example:
        >>> client = GeminiCloudClient.from_env()
        >>> response = await client.generate_content("Hello, world!")
        >>> print(response.text)
    """

    def __init__(self, config: GeminiConfig | None = None):
        self.config = config or GeminiConfig.from_env()
        self.authenticator = GeminiAuthenticator(self.config)
        self._session: Any | None = None
        self._request_count = 0
        self._hooks: dict[str, list[Callable]] = {
            "pre_request": [],
            "post_request": [],
            "on_error": [],
        }

        # Validate config on init
        issues = self.config.validate()
        if issues and not self.config.mock_responses:
            logger.warning(f"Configuration issues: {issues}")

    @classmethod
    def from_env(cls) -> GeminiCloudClient:
        """Create client from environment variables."""
        return cls(GeminiConfig.from_env())

    def add_hook(self, event: str, callback: Callable[..., Any]) -> None:
        """Add a hook for request lifecycle events."""
        if event in self._hooks:
            self._hooks[event].append(callback)

    async def _run_hooks(self, event: str, **kwargs: Any) -> None:
        """Run all hooks for an event."""
        for hook in self._hooks.get(event, []):
            try:
                result = hook(**kwargs)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Hook error ({event}): {e}")

    async def _get_session(self) -> Any:
        """Get or create HTTP session."""
        if self._session is None:
            if HAS_HTTPX:
                self._session = httpx.AsyncClient(timeout=self.config.timeout_seconds)
            elif HAS_AIOHTTP:
                self._session = aiohttp.ClientSession()
            else:
                raise RuntimeError("No HTTP client available. Install httpx or aiohttp.")
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> GeminiCloudClient:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        await self.close()

    def _build_url(self, endpoint: str) -> str:
        """Build full URL for an endpoint."""
        base = self.config.base_url.rstrip("/")
        return f"{base}/{endpoint}"

    async def generate_content(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_instruction: str | None = None,
        **kwargs: Any,
    ) -> GeminiResponse:
        """Generate content using Gemini model.

        Args:
            prompt: The input prompt
            model: Model name (defaults to config model)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum output tokens
            system_instruction: Optional system instruction
            **kwargs: Additional generation parameters

        Returns:
            GeminiResponse with generated content
        """
        # Pre-deployment mock mode
        if self.config.mock_responses or self.config.pending_deployment:
            logger.info("Using mock response (app not deployed yet)")
            return GeminiResponse.mock_response(prompt)

        model_name = model or self.config.model_name
        endpoint = f"models/{model_name}:generateContent"

        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        # Merge additional kwargs
        if kwargs:
            payload["generationConfig"].update(kwargs)

        return await self._request("POST", endpoint, payload)

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: Any,
    ) -> GeminiResponse:
        """Multi-turn chat conversation.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name
            **kwargs: Additional parameters

        Returns:
            GeminiResponse with chat completion
        """
        if self.config.mock_responses or self.config.pending_deployment:
            last_msg = messages[-1].get("content", "") if messages else ""
            return GeminiResponse.mock_response(last_msg)

        model_name = model or self.config.model_name
        endpoint = f"models/{model_name}:generateContent"

        contents = []
        for msg in messages:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

        payload = {
            "contents": contents,
            "generationConfig": kwargs.get("generation_config", {}),
        }

        return await self._request("POST", endpoint, payload)

    async def embed_content(
        self,
        text: str | list[str],
        model: str = "embedding-001",
    ) -> GeminiResponse:
        """Generate embeddings for text.

        Args:
            text: Single text or list of texts to embed
            model: Embedding model name

        Returns:
            GeminiResponse with embeddings
        """
        if self.config.mock_responses or self.config.pending_deployment:
            return GeminiResponse(
                success=True,
                data={"embeddings": [[0.0] * 768]},  # Mock embedding
                status_code=200,
            )

        endpoint = f"models/{model}:embedContent"

        if isinstance(text, str):
            text = [text]

        payload = {"content": {"parts": [{"text": t} for t in text]}}

        return await self._request("POST", endpoint, payload)

    async def _request(
        self,
        method: str,
        endpoint: str,
        payload: dict[str, Any] | None = None,
    ) -> GeminiResponse:
        """Make an API request to Gemini."""
        import time

        await self._run_hooks("pre_request", endpoint=endpoint, payload=payload)

        url = self._build_url(endpoint)
        headers = await self.authenticator.get_headers()
        params = self.authenticator.get_query_params()

        start_time = time.time()

        try:
            session = await self._get_session()

            if HAS_HTTPX:
                response = await session.request(
                    method,
                    url,
                    json=payload,
                    headers=headers,
                    params=params,
                )
                status_code = response.status_code
                response_data = response.json()
            elif HAS_AIOHTTP:
                async with session.request(
                    method,
                    url,
                    json=payload,
                    headers=headers,
                    params=params,
                ) as response:
                    status_code = response.status
                    response_data = await response.json()
            else:
                return GeminiResponse.error_response("No HTTP client available")

            latency = (time.time() - start_time) * 1000

            if status_code >= 400:
                error_msg = response_data.get("error", {}).get("message", "Unknown error")
                result = GeminiResponse.error_response(error_msg, status_code)
            else:
                result = GeminiResponse.from_api_response(response_data, latency)

            await self._run_hooks("post_request", response=result)
            self._request_count += 1

            return result

        except Exception as e:
            error_result = GeminiResponse.error_response(str(e))
            await self._run_hooks("on_error", error=e)
            return error_result

    async def health_check(self) -> dict[str, Any]:
        """Check connectivity and configuration status."""
        return {
            "config_valid": len(self.config.validate()) == 0,
            "pending_deployment": self.config.pending_deployment,
            "mock_mode": self.config.mock_responses,
            "environment": self.config.environment.value,
            "model": self.config.model_name,
            "request_count": self._request_count,
            "studio_url": self.config.studio_project_url,
        }


# Convenience function for quick access
@lru_cache(maxsize=1)
def get_gemini_client() -> GeminiCloudClient:
    """Get cached Gemini client instance."""
    return GeminiCloudClient.from_env()


# Sync wrapper for non-async code
def generate_content_sync(prompt: str, **kwargs: Any) -> GeminiResponse:
    """Synchronous wrapper for generate_content."""
    client = get_gemini_client()
    return asyncio.run(client.generate_content(prompt, **kwargs))


__all__ = [
    "GeminiCloudClient",
    "GeminiConfig",
    "GeminiResponse",
    "GeminiEnvironment",
    "AuthMethod",
    "GeminiAuthenticator",
    "get_gemini_client",
    "generate_content_sync",
]
