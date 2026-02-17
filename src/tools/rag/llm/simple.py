"""Simple fallback LLM provider."""

from typing import Any

from .base import BaseLLMProvider


class SimpleLLM(BaseLLMProvider):
    """Simple rule-based LLM for fallback.

    This is a basic fallback that should not be used for production.
    Use Ollama models instead.
    """

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate a simple response based on prompt.

        Args:
            prompt: Input prompt
            system: Optional system message (ignored)
            temperature: Sampling temperature (ignored)
            max_tokens: Maximum tokens (ignored)
            **kwargs: Additional parameters (ignored)

        Returns:
            Simple fallback response
        """
        if "?" in prompt:
            question_start = prompt.rfind("Question:") + 9
            if question_start > 8:
                question = prompt[question_start:].strip()
                return (
                    f"Based on the provided context, here's an answer to: {question}\n\n"
                    "This is a simple fallback response. For better answers, "
                    "please configure an LLM provider like Ollama (ministral or gpt-oss-safeguard)."
                )

        return (
            "This is a simple fallback LLM response. "
            "Please configure an actual LLM provider (Ollama) for better results."
        )

    def stream(self, prompt: str, system: str | None = None, temperature: float = 0.7, **kwargs: Any) -> Any:
        """Stream simple response.

        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Yields:
            Text chunks
        """
        response = self.generate(prompt, system, temperature, **kwargs)
        # Yield response in chunks
        words = response.split()
        for word in words:
            yield word + " "

    async def async_generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text completion (async).

        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens (ignored)
            **kwargs: Additional parameters

        Returns:
            Simple fallback response
        """
        return self.generate(prompt, system, temperature, max_tokens, **kwargs)

    async def async_stream(
        self, prompt: str, system: str | None = None, temperature: float = 0.7, **kwargs: Any
    ) -> Any:
        """Stream text generation (async).

        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Yields:
            Text chunks
        """
        for chunk in self.stream(prompt, system, temperature, **kwargs):
            yield chunk
