"""Mistral AI LLM provider."""

import logging
from typing import Any, AsyncGenerator

from tools.rag.resilience import get_circuit_breaker

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class MistralLLM(BaseLLMProvider):
    """Mistral AI LLM provider for Mistral models (mistral-large, mistral-small, etc.).

    Uses the official Mistral AI Python client.
    """

    def __init__(
        self,
        model: str = "mistral-large-latest",
        api_key: str | None = None,
        server_url: str | None = None,
        timeout: float = 120.0,
    ):
        """Initialize Mistral LLM provider.

        Args:
            model: Model name (mistral-large-latest, mistral-small-latest, etc.)
            api_key: Mistral API key (if None, uses MISTRAL_API_KEY env var)
            server_url: Optional custom server URL for self-hosted deployments
            timeout: Request timeout in seconds
        """
        self.model = model
        self.api_key = api_key
        self.server_url = server_url
        self.timeout = timeout
        self._client = None
        self._breaker = get_circuit_breaker("mistral")

    def _get_client(self):
        """Lazy load Mistral sync client."""
        if self._client is None:
            try:
                from mistralai import Mistral

                kwargs: dict[str, Any] = {}
                if self.api_key:
                    kwargs["api_key"] = self.api_key
                if self.server_url:
                    kwargs["server_url"] = self.server_url

                self._client = Mistral(**kwargs)
            except ImportError:
                raise ImportError(
                    "Mistral AI library not installed. Install with: pip install mistralai"
                ) from None
        return self._client

    def _get_async_client(self):
        """Return the Mistral client (same instance handles sync and async)."""
        return self._get_client()

    def _build_messages(self, prompt: str, system: str | None = None) -> list[dict[str, str]]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return messages

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using Mistral AI API."""
        client = self._get_client()
        messages = self._build_messages(prompt, system)

        try:
            with self._breaker:
                response = client.chat.complete(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"Mistral AI API error: {e}") from e

    def stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """Stream text generation from Mistral AI API."""
        client = self._get_client()
        messages = self._build_messages(prompt, system)

        try:
            with self._breaker:
                stream = client.chat.stream(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )

                for chunk in stream:
                    if chunk.data.choices[0].delta.content:
                        yield chunk.data.choices[0].delta.content
        except Exception as e:
            raise RuntimeError(f"Mistral AI streaming error: {e}") from e

    async def async_generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using async Mistral AI API."""
        client = self._get_async_client()
        messages = self._build_messages(prompt, system)

        try:
            with self._breaker:
                response = await client.chat.complete_async(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"Mistral AI async API error: {e}") from e

    async def async_stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str]:
        """Stream text generation using async Mistral AI API."""
        client = self._get_async_client()
        messages = self._build_messages(prompt, system)

        try:
            with self._breaker:
                stream = await client.chat.stream_async(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )

                async for chunk in stream:
                    if chunk.data.choices[0].delta.content:
                        yield chunk.data.choices[0].delta.content
        except Exception as e:
            raise RuntimeError(f"Mistral AI async streaming error: {e}") from e
