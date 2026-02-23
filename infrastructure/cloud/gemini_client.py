"""
Gemini Studio Cloud Client

Async client for Google Gemini Studio integration with:
- Retry logic with exponential backoff
- Streaming response support
- Configuration via environment variables
- Seamless integration with grid Settings

Usage:
    client = GeminiStudioClient()
    response = await client.generate("Your prompt here")

    # Streaming
    async for chunk in client.stream("Your prompt"):
        print(chunk, end="")
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    import httpx as httpx_typing

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore


logger = logging.getLogger(__name__)

T = TypeVar("T")


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes", "y", "on"}


def _is_production_environment() -> bool:
    env = (
        os.getenv("MOTHERSHIP_ENVIRONMENT")
        or os.getenv("GRID_ENVIRONMENT")
        or os.getenv("ENVIRONMENT")
        or os.getenv("ENV")
        or "development"
    )
    return env.strip().lower() in {"production", "prod"}


class GeminiModel(StrEnum):
    """Available Gemini models."""

    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_2_0_FLASH = "gemini-2.0-flash-exp"


@dataclass
class GeminiConfig:
    """Configuration for Gemini Studio client."""

    api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    project_id: str = field(default_factory=lambda: os.getenv("GEMINI_PROJECT_ID", ""))
    location: str = field(default_factory=lambda: os.getenv("GEMINI_LOCATION", "us-central1"))
    model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", GeminiModel.GEMINI_1_5_PRO.value))

    # Retry configuration
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0

    # Request configuration
    timeout: float = 120.0
    temperature: float = 0.7
    max_output_tokens: int = 8192
    top_p: float = 0.95
    top_k: int = 40

    # Endpoint (for custom deployments / AI Studio)
    studio_endpoint: str = field(
        default_factory=lambda: os.getenv("GEMINI_STUDIO_ENDPOINT", "https://generativelanguage.googleapis.com/v1beta")
    )

    def validate(self) -> bool:
        """Validate required configuration."""
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set - client will operate in dry-run mode")
            return False
        return True


class GeminiError(Exception):
    """Base exception for Gemini client errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: Any | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class GeminiRateLimitError(GeminiError):
    """Rate limit exceeded."""

    pass


class GeminiAuthError(GeminiError):
    """Authentication failed."""

    pass


class GeminiConnectionError(GeminiError):
    """Connection failed."""

    pass


def with_retry[T](func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Decorator for retry logic with exponential backoff."""

    @wraps(func)
    async def wrapper(self: GeminiStudioClient, *args: Any, **kwargs: Any) -> T:
        last_exception: Exception | None = None
        delay = self.config.base_delay

        for attempt in range(self.config.max_retries + 1):
            try:
                result = await func(self, *args, **kwargs)
                return result
            except GeminiRateLimitError as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    logger.warning(
                        f"Rate limited (attempt {attempt + 1}/{self.config.max_retries + 1}), "
                        f"retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * self.config.backoff_multiplier, self.config.max_delay)
            except GeminiConnectionError as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    logger.warning(
                        f"Connection error (attempt {attempt + 1}/{self.config.max_retries + 1}), "
                        f"retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * self.config.backoff_multiplier, self.config.max_delay)
            except GeminiAuthError:
                raise
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error: {e}")
                if attempt < self.config.max_retries:
                    await asyncio.sleep(delay)
                    delay = min(delay * self.config.backoff_multiplier, self.config.max_delay)

        raise last_exception or GeminiError("Max retries exceeded")

    return wrapper  # type: ignore


@dataclass
class GenerationResult:
    """Result from a generation request."""

    text: str
    model: str
    finish_reason: str | None = None
    usage: dict[str, int] | None = None
    safety_ratings: list[dict[str, Any]] | None = None
    raw_response: Any | None = None
    origin: str = "live"
    degraded: bool = False
    provider_latency_ms: float = 0.0

    @property
    def prompt_tokens(self) -> int:
        if not self.usage:
            return 0
        return self.usage.get("prompt_token_count", self.usage.get("promptTokenCount", 0))

    @property
    def completion_tokens(self) -> int:
        if not self.usage:
            return 0
        return self.usage.get("candidates_token_count", self.usage.get("candidatesTokenCount", 0))

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class GeminiStudioClient:
    """
    Async client for Gemini Studio / Google AI Studio integration.

    Supports both direct API calls and streaming responses with
    automatic retry logic and exponential backoff.
    """

    def __init__(
        self,
        config: GeminiConfig | None = None,
        api_key: str | None = None,
    ):
        self.config = config or GeminiConfig()
        if api_key:
            self.config.api_key = api_key

        self._http_client: httpx_typing.AsyncClient | None = None
        self._initialized = False
        self._dry_run = not self.config.validate()

        allow_dry_run_in_production = _parse_bool(
            os.getenv("GEMINI_STUDIO_ALLOW_DRY_RUN_IN_PRODUCTION"),
            False,
        )
        if self._dry_run and _is_production_environment() and not allow_dry_run_in_production:
            raise RuntimeError(
                "GeminiStudioClient dry-run mode is forbidden in production. "
                "Set GEMINI_API_KEY or explicitly allow with GEMINI_STUDIO_ALLOW_DRY_RUN_IN_PRODUCTION=true."
            )

    async def __aenter__(self) -> GeminiStudioClient:
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def initialize(self) -> None:
        """Initialize the HTTP client."""
        if self._initialized:
            return

        if httpx is None:
            raise ImportError("httpx is required for GeminiStudioClient. Install with: pip install httpx")

        assert httpx is not None
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout),
            headers={
                "Content-Type": "application/json",
            },
        )
        self._initialized = True
        logger.info(f"GeminiStudioClient initialized (model={self.config.model}, dry_run={self._dry_run})")

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        self._initialized = False

    def _build_url(self, action: str = "generateContent") -> str:
        """Build the API endpoint URL."""
        return f"{self.config.studio_endpoint}/models/{self.config.model}:{action}"

    def _build_payload(
        self,
        prompt: str,
        system_instruction: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build the request payload."""
        contents = [{"parts": [{"text": prompt}]}]

        generation_config = {
            "temperature": kwargs.get("temperature", self.config.temperature),
            "maxOutputTokens": kwargs.get("max_tokens", self.config.max_output_tokens),
            "topP": kwargs.get("top_p", self.config.top_p),
            "topK": kwargs.get("top_k", self.config.top_k),
        }

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        return payload

    def _handle_error_response(self, status_code: int, response_data: Any) -> None:
        """Handle error responses from the API."""
        error_msg = "Unknown error"
        if isinstance(response_data, dict):
            error_info = response_data.get("error", {})
            error_msg = error_info.get("message", str(response_data))

        if status_code == 401 or status_code == 403:
            raise GeminiAuthError(f"Authentication failed: {error_msg}", status_code, response_data)
        elif status_code == 429:
            raise GeminiRateLimitError(f"Rate limit exceeded: {error_msg}", status_code, response_data)
        elif status_code >= 500:
            raise GeminiConnectionError(f"Server error: {error_msg}", status_code, response_data)
        else:
            raise GeminiError(f"API error ({status_code}): {error_msg}", status_code, response_data)

    def _parse_response(self, data: dict[str, Any]) -> GenerationResult:
        """Parse the API response into a GenerationResult."""
        candidates = data.get("candidates", [])
        if not candidates:
            return GenerationResult(
                text="",
                model=self.config.model,
                finish_reason="NO_CANDIDATES",
                raw_response=data,
                origin="live",
            )

        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        text = "".join(part.get("text", "") for part in parts)

        return GenerationResult(
            text=text,
            model=self.config.model,
            finish_reason=candidate.get("finishReason"),
            usage=data.get("usageMetadata"),
            safety_ratings=candidate.get("safetyRatings"),
            raw_response=data,
            origin="live",
        )

    @with_retry
    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """
        Generate content from the Gemini model.

        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction
            **kwargs: Additional generation parameters

        Returns:
            GenerationResult with the model's response
        """
        if self._dry_run:
            raise GeminiAuthError(
                "Gemini API key not configured. Set GEMINI_API_KEY environment variable to enable Gemini."
            )

        if not self._initialized:
            await self.initialize()

        assert self._http_client is not None
        assert httpx is not None

        url = self._build_url("generateContent")
        payload = self._build_payload(prompt, system_instruction, **kwargs)

        assert httpx is not None
        try:
            response = await self._http_client.post(
                url,
                json=payload,
                params={"key": self.config.api_key},
            )
        except httpx.ConnectError as e:
            raise GeminiConnectionError(f"Failed to connect: {e}") from e
        except httpx.TimeoutException as e:
            raise GeminiConnectionError(f"Request timed out: {e}") from e

        if response.status_code != 200:
            self._handle_error_response(response.status_code, response.json())

        return self._parse_response(response.json())

    async def stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream content from the Gemini model.

        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction
            **kwargs: Additional generation parameters

        Yields:
            Text chunks as they are received
        """
        if self._dry_run:
            raise GeminiAuthError(
                "Gemini API key not configured. Set GEMINI_API_KEY environment variable to enable Gemini."
            )

        if not self._initialized:
            await self.initialize()

        assert self._http_client is not None
        assert httpx is not None

        url = self._build_url("streamGenerateContent")
        payload = self._build_payload(prompt, system_instruction, **kwargs)

        assert httpx is not None
        try:
            async with self._http_client.stream(
                "POST",
                url,
                json=payload,
                params={"key": self.config.api_key, "alt": "sse"},
            ) as response:
                if response.status_code != 200:
                    data = await response.aread()
                    self._handle_error_response(response.status_code, json.loads(data))

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for part in parts:
                                    if text := part.get("text"):
                                        yield text
                        except json.JSONDecodeError:
                            continue

        except httpx.ConnectError as e:
            raise GeminiConnectionError(f"Failed to connect: {e}") from e
        except httpx.TimeoutException as e:
            raise GeminiConnectionError(f"Request timed out: {e}") from e

    async def chat(
        self,
        messages: list[dict[str, str]],
        system_instruction: str | None = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """
        Multi-turn chat with the Gemini model.

        Args:
            messages: List of {"role": "user"|"model", "content": "..."} dicts
            system_instruction: Optional system instruction
            **kwargs: Additional generation parameters

        Returns:
            GenerationResult with the model's response
        """
        if self._dry_run:
            raise GeminiAuthError(
                "Gemini API key not configured. Set GEMINI_API_KEY environment variable to enable Gemini."
            )

        if not self._initialized:
            await self.initialize()

        assert self._http_client is not None
        assert httpx is not None

        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                {
                    "role": role,
                    "parts": [{"text": msg["content"]}],
                }
            )

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "maxOutputTokens": kwargs.get("max_tokens", self.config.max_output_tokens),
                "topP": kwargs.get("top_p", self.config.top_p),
                "topK": kwargs.get("top_k", self.config.top_k),
            },
        }

        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        url = self._build_url("generateContent")

        assert httpx is not None
        try:
            response = await self._http_client.post(
                url,
                json=payload,
                params={"key": self.config.api_key},
            )
        except httpx.ConnectError as e:
            raise GeminiConnectionError(f"Failed to connect: {e}") from e

        if response.status_code != 200:
            self._handle_error_response(response.status_code, response.json())

        return self._parse_response(response.json())

    def health_check(self) -> dict[str, Any]:
        """Return client health status."""
        return {
            "initialized": self._initialized,
            "dry_run": self._dry_run,
            "degraded": self._dry_run,
            "origin": "dry_run" if self._dry_run else "live",
            "model": self.config.model,
            "endpoint": self.config.studio_endpoint,
            "has_api_key": bool(self.config.api_key),
            "project_id": self.config.project_id or "not_set",
        }


# Convenience function for quick usage
async def generate(
    prompt: str,
    api_key: str | None = None,
    model: str = GeminiModel.GEMINI_1_5_PRO.value,
    **kwargs: Any,
) -> str:
    """
    Quick generation helper.

    Example:
        text = await generate("Explain quantum computing", api_key="...")
    """
    config = GeminiConfig(model=model)
    if api_key:
        config.api_key = api_key

    async with GeminiStudioClient(config=config) as client:
        result = await client.generate(prompt, **kwargs)
        return result.text


__all__ = [
    "GeminiStudioClient",
    "GeminiConfig",
    "GeminiModel",
    "GeminiError",
    "GeminiRateLimitError",
    "GeminiAuthError",
    "GeminiConnectionError",
    "GenerationResult",
    "generate",
]
