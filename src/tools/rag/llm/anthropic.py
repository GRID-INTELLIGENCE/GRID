"""Anthropic LLM provider."""

from typing import Any, AsyncGenerator

from .base import BaseLLMProvider


class AnthropicLLM(BaseLLMProvider):
    """Anthropic LLM provider for Claude models (Claude 3.5 Sonnet, Claude 3 Opus, etc.).

    Uses the official Anthropic Python client.
    """

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 120.0,
    ):
        """Initialize Anthropic LLM provider.

        Args:
            model: Model name (claude-3-5-sonnet-20241022, claude-3-opus-20240229, etc.)
            api_key: Anthropic API key (if None, uses ANTHROPIC_API_KEY env var)
            base_url: Optional custom base URL
            timeout: Request timeout in seconds
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._client = None

    def _get_client(self):
        """Lazy load Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic

                client_kwargs = {"api_key": self.api_key} if self.api_key else {}
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url

                self._client = Anthropic(**client_kwargs)
            except ImportError:
                raise ImportError("Anthropic library not installed. Install with: pip install anthropic") from None
        return self._client

    def _get_async_client(self):
        """Lazy load async Anthropic client."""
        try:
            from anthropic import AsyncAnthropic

            client_kwargs = {"api_key": self.api_key} if self.api_key else {}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            return AsyncAnthropic(**client_kwargs)
        except ImportError:
            raise ImportError("Anthropic library not installed. Install with: pip install anthropic") from None

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using Anthropic API.

        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        client = self._get_client()

        # Set default max_tokens if not provided (Anthropic requires this)
        if max_tokens is None:
            max_tokens = 1024

        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                timeout=self.timeout,
                **kwargs,
            )
            return message.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {e}") from e

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

        # Set default max_tokens if not provided
        if max_tokens is None:
            max_tokens = 1024

        try:
            with client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                timeout=self.timeout,
                **kwargs,
            ) as stream:
                yield from stream.text_stream
        except Exception as e:
            raise RuntimeError(f"Anthropic streaming error: {e}") from e

    async def async_generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using async Anthropic API.

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

        # Set default max_tokens if not provided
        if max_tokens is None:
            max_tokens = 1024

        try:
            message = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                timeout=self.timeout,
                **kwargs,
            )
            return message.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic async API error: {e}") from e

    async def async_stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str]:
        """Stream text generation using async Anthropic API.

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

        # Set default max_tokens if not provided
        if max_tokens is None:
            max_tokens = 1024

        try:
            async with client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                timeout=self.timeout,
                **kwargs,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise RuntimeError(f"Anthropic async streaming error: {e}") from e
