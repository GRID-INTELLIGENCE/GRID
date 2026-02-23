"""OpenAI LLM provider for RAG.

Uses the OpenAI API (or any OpenAI-compatible endpoint via base_url) for chat completions.
"""

from __future__ import annotations

from typing import Any

from .base import BaseLLMProvider


class OpenAILLM(BaseLLMProvider):
    """OpenAI (or OpenAI-compatible) LLM provider."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
    ):
        """Initialize OpenAI LLM provider.

        Args:
            model: Model name (e.g. gpt-4o-mini, gpt-4o).
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var).
            base_url: Optional base URL for proxy or custom endpoint (e.g. LiteLLM).
            timeout: Request timeout in seconds.
        """
        import os

        self.model = model
        self.api_key = (api_key or os.getenv("OPENAI_API_KEY") or "").strip()
        self.base_url = base_url
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI LLM")

    def _client(self) -> Any:
        """Lazy OpenAI client."""
        from openai import OpenAI

        kwargs: dict[str, Any] = {"api_key": self.api_key, "timeout": self.timeout}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return OpenAI(**kwargs)

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using OpenAI chat completions."""
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        client = self._client()
        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
            **kwargs,
        )
        return (resp.choices[0].message.content or "").strip()

    def stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> Any:
        """Stream text using OpenAI chat completions."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        client = self._client()
        stream = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True,
            **kwargs,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def async_generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text (async) using OpenAI chat completions."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        from openai import AsyncOpenAI

        client_kwargs: dict[str, Any] = {"api_key": self.api_key, "timeout": self.timeout}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        client = AsyncOpenAI(**client_kwargs)
        resp = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
            **kwargs,
        )
        return (resp.choices[0].message.content or "").strip()

    async def async_stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> Any:
        """Stream text (async) using OpenAI chat completions."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        from openai import AsyncOpenAI

        client_kwargs = {"api_key": self.api_key, "timeout": self.timeout}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        client = AsyncOpenAI(**client_kwargs)
        stream = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
