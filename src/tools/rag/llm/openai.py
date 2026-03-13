"""OpenAI LLM provider."""

import logging
from typing import Any, AsyncGenerator

from tools.rag.resilience import get_circuit_breaker

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAILLM(BaseLLMProvider):
    """OpenAI LLM provider for GPT models (GPT-4, GPT-4o, GPT-3.5, etc.).

    Uses the official OpenAI Python client.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 120.0,
    ):
        """Initialize OpenAI LLM provider.

        Args:
            model: Model name (gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo, etc.)
            api_key: OpenAI API key (if None, uses OPENAI_API_KEY env var)
            base_url: Optional custom base URL for OpenAI-compatible APIs
            timeout: Request timeout in seconds
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._client = None
        self._breaker = get_circuit_breaker("openai")

    def _get_client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI

                client_kwargs = {"api_key": self.api_key} if self.api_key else {}
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url

                self._client = OpenAI(**client_kwargs)
            except ImportError:
                raise ImportError("OpenAI library not installed. Install with: pip install openai") from None
        return self._client

    def _get_async_client(self):
        """Lazy load async OpenAI client."""
        try:
            from openai import AsyncOpenAI

            client_kwargs = {"api_key": self.api_key} if self.api_key else {}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            return AsyncOpenAI(**client_kwargs)
        except ImportError:
            raise ImportError("OpenAI library not installed. Install with: pip install openai") from None

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using OpenAI API.

        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters (top_p, frequency_penalty, etc.)

        Returns:
            Generated text
        """
        client = self._get_client()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            with self._breaker:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=self.timeout,
                    **kwargs,
                )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}") from e

    def stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """Stream text generation.

        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Yields:
            Text chunks as they are generated
        """
        client = self._get_client()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            with self._breaker:
                stream = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    timeout=self.timeout,
                    **kwargs,
                )

                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
        except Exception as e:
            raise RuntimeError(f"OpenAI streaming error: {e}") from e

    async def async_generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using async OpenAI API.

        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        client = self._get_async_client()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            with self._breaker:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=self.timeout,
                    **kwargs,
                )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"OpenAI async API error: {e}") from e

    async def async_stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str]:
        """Stream text generation using async OpenAI API.

        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Yields:
            Text chunks as they are generated
        """
        client = self._get_async_client()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            with self._breaker:
                stream = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    timeout=self.timeout,
                    **kwargs,
                )

                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
        except Exception as e:
            raise RuntimeError(f"OpenAI async streaming error: {e}") from e
