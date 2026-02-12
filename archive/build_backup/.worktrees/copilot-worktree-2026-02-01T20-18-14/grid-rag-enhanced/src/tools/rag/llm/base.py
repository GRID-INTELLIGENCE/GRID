"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Any


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text completion.

        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model-specific parameters

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    def stream(self, prompt: str, system: str | None = None, temperature: float = 0.7, **kwargs: Any) -> Any:
        """Stream text generation."""
        pass

    @abstractmethod
    async def async_generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text completion (async)."""
        pass

    @abstractmethod
    async def async_stream(
        self, prompt: str, system: str | None = None, temperature: float = 0.7, **kwargs: Any
    ) -> Any:
        """Stream text generation (async)."""
        pass
