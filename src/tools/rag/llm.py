"""LLM providers for RAG."""

import asyncio
import logging
import subprocess
from typing import Any

from grid.services.llm.llm_client import LLMConfig, OllamaNativeClient

logger = logging.getLogger(__name__)

from tools.rag.types import LLMProvider, LLMProviderError


class OllamaLLM(LLMProvider):
    """Wrapper for Ollama language models."""

    def __init__(self, model: str = "llama2"):
        self.model = model
        self._native_client = None

    def _get_native_client(self):
        if self._native_client is None:
            self._native_client = OllamaNativeClient()
        return self._native_client

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using Ollama (sync version).

        Note: For async contexts, prefer async_generate() which uses
        non-blocking subprocess calls.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (ignored in sync version)

        Returns:
            Generated text or error message
        """
        try:
            result = subprocess.run(  # noqa: S603 subprocess call is intentional
                ["ollama", "run", self.model, prompt],  # noqa: S607 partial path is intentional
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired as e:
            logger.error(f"Ollama LLM timed out after 60s for model {self.model}")
            raise LLMProviderError(f"Ollama request timed out for {self.model}") from e
        except Exception as e:
            logger.error(f"Ollama LLM error: {e}")
            raise LLMProviderError(f"Failed to generate response using Ollama model {self.model}: {e}") from e

    async def async_generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using Ollama (async version).

        Tries native client first, falls back to async subprocess.
        """
        # Try native client first
        try:
            client = self._get_native_client()
            resp = await client.generate(prompt, config=LLMConfig(model=self.model))
            return resp.content
        except Exception as e:
            logger.debug(f"Native client failed, trying subprocess: {e}")

        # Fallback to async subprocess (safe: argv from code, no exec())
        try:
            proc = await asyncio.create_subprocess_exec(
                "ollama",
                "run",
                self.model,
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            async with asyncio.timeout(60):
                stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                return stdout.decode("utf-8", errors="replace").strip()
            else:
                err_msg = stderr.decode("utf-8", errors="replace")
                logger.error(f"Ollama subprocess failed: {err_msg}")
                raise LLMProviderError(f"Ollama returned non-zero exit code for {self.model}: {err_msg}")
        except LLMProviderError:
            raise
        except TimeoutError as e:
            logger.error(f"Ollama async LLM timed out after 60s for model {self.model}")
            raise LLMProviderError(f"Ollama async request timed out for {self.model}") from e
        except Exception as e:
            logger.error(f"Ollama async LLM error: {e}")
            raise LLMProviderError(f"Failed to generate async response using Ollama model {self.model}: {e}") from e


class OpenAILLM(LLMProvider):
    """Wrapper for OpenAI's language models."""

    def __init__(self, model: str = "gpt-3.5-turbo", api_key: str | None = None):
        self.model = model
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self.api_key) if self.api_key else None
            except ImportError:
                logger.warning("OpenAI library not installed, OpenAI provider unavailable")
                self._client = None
        return self._client

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using OpenAI API.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text

        Raises:
            LLMProviderError: If the OpenAI library is missing, API key is absent, or the call fails.
        """
        client = self._get_client()
        if client is None:
            raise LLMProviderError(
                "OpenAI library not installed or no API key provided. "
                "Install with: uv add openai, and set OPENAI_API_KEY."
            )

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 500),
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI LLM error: {e}")
            raise LLMProviderError(f"Failed to generate response using OpenAI model {self.model}: {e}") from e


class SimpleLLM(LLMProvider):
    """Simple rule-based LLM for fallback."""

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
        # Extract question from prompt
        if "?" in prompt:
            question_start = prompt.rfind("Question:") + 9
            if question_start > 8:
                question = prompt[question_start:].strip()
                return f"Based on the provided context, here's an answer to: {question}\n\nThis is a simple fallback response. For better answers, please configure an LLM provider like Ollama or OpenAI."

        return "This is a simple fallback LLM response. Please configure an actual LLM provider for better results."

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
        """Async wrapper for sync generate.

        Args:
            prompt: Input prompt
            system: Optional system message (ignored)
            temperature: Sampling temperature (ignored)
            max_tokens: Maximum tokens (ignored)
            **kwargs: Additional parameters (ignored)

        Returns:
            Simple fallback response
        """
        return self.generate(prompt, system, temperature, max_tokens, **kwargs)

    async def async_stream(
        self, prompt: str, system: str | None = None, temperature: float = 0.7, **kwargs: Any
    ) -> Any:
        """Async stream wrapper.

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


def get_llm_provider(provider_type: str = "simple", **kwargs) -> LLMProvider:
    """Get an LLM provider by type.

    Args:
        provider_type: Type of provider ("simple", "ollama", "openai")
        **kwargs: Additional arguments for the provider

    Returns:
        LLMProvider instance
    """
    providers = {"simple": SimpleLLM, "ollama": OllamaLLM, "openai": OpenAILLM}

    if provider_type not in providers:
        raise ValueError(f"Unknown provider type: {provider_type}")

    return providers[provider_type](**kwargs)
