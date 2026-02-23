"""Anthropic Claude LLM provider for RAG."""

from __future__ import annotations

from typing import Any

from .base import BaseLLMProvider


class AnthropicLLM(BaseLLMProvider):
    """Anthropic Claude LLM provider."""

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: str | None = None,
        timeout: float = 60.0,
    ):
        """Initialize Anthropic LLM provider.

        Args:
            model: Model name (e.g. claude-3-5-sonnet-20241022).
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var).
            timeout: Request timeout in seconds.
        """
        import os

        self.model = model
        self.api_key = (api_key or os.getenv("ANTHROPIC_API_KEY") or "").strip()
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic LLM")

    def _client(self) -> Any:
        """Lazy Anthropic client."""
        from anthropic import Anthropic

        return Anthropic(api_key=self.api_key, timeout=self.timeout)

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using Anthropic messages API."""
        client = self._client()
        resp = client.messages.create(
            model=self.model,
            max_tokens=max_tokens or 4096,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            **kwargs,
        )
        if resp.content and len(resp.content) > 0:
            block = resp.content[0]
            if hasattr(block, "text"):
                return block.text.strip()
        return ""

    def stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> Any:
        """Stream text using Anthropic messages API."""
        client = self._client()
        system_text = system or ""
        with client.messages.stream(
            model=self.model,
            max_tokens=4096,
            system=system_text,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            **kwargs,
        ) as stream:
            yield from stream.text_stream

    async def async_generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text (async) using Anthropic messages API."""
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key, timeout=self.timeout)
        resp = await client.messages.create(
            model=self.model,
            max_tokens=max_tokens or 4096,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            **kwargs,
        )
        if resp.content and len(resp.content) > 0:
            block = resp.content[0]
            if hasattr(block, "text"):
                return block.text.strip()
        return ""

    async def async_stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> Any:
        """Stream text (async) using Anthropic messages API."""
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key, timeout=self.timeout)
        async with client.messages.stream(
            model=self.model,
            max_tokens=4096,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            **kwargs,
        ) as stream:
            async for text in stream.text_stream:
                yield text
