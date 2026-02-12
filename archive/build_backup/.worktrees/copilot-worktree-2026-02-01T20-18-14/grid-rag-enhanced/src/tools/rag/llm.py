"""LLM providers for RAG."""

import subprocess

from grid.services.llm.llm_client import LLMConfig, OllamaNativeClient

from .types import LLMProvider


class OllamaLLM(LLMProvider):
    """Wrapper for Ollama language models."""

    def __init__(self, model: str = "llama2"):
        self.model = model
        self._native_client = None

    def _get_native_client(self):
        if self._native_client is None:
            self._native_client = OllamaNativeClient()
        return self._native_client

    def generate(self, prompt: str) -> str:
        """Generate text using Ollama."""
        try:
            result = subprocess.run(
                ["ollama", "run", self.model, prompt], capture_output=True, text=True, check=True, timeout=60
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"Ollama LLM error: {e}")
            return f"Error: Could not generate response using {self.model}"

    async def async_generate(self, prompt: str) -> str:
        """Generate text using Ollama (native async)."""
        try:
            client = self._get_native_client()
            resp = await client.generate(prompt, config=LLMConfig(model=self.model))
            return resp.content
        except Exception as e:
            print(f"Ollama Native LLM error: {e}")
            return f"Error: Native client failed for {self.model}"


class OpenAILLM(LLMProvider):
    """Wrapper for OpenAI's language models."""

    def __init__(self, model: str = "gpt-3.5-turbo", api_key: str | None = None):
        self.model = model
        self.api_key = api_key

    def generate(self, prompt: str) -> str:
        """Generate text using OpenAI API."""
        try:
            import openai

            if self.api_key:
                openai.api_key = self.api_key

            response = openai.ChatCompletion.create(
                model=self.model, messages=[{"role": "user", "content": prompt}], temperature=0.7, max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI LLM error: {e}")
            return f"Error: Could not generate response using {self.model}"


class SimpleLLM(LLMProvider):
    """Simple rule-based LLM for fallback."""

    def generate(self, prompt: str) -> str:
        """Generate a simple response based on prompt."""
        # Extract question from prompt
        if "?" in prompt:
            question_start = prompt.rfind("Question:") + 9
            if question_start > 8:
                question = prompt[question_start:].strip()
                return f"Based on the provided context, here's an answer to: {question}\n\nThis is a simple fallback response. For better answers, please configure an LLM provider like Ollama or OpenAI."

        return "This is a simple fallback LLM response. Please configure an actual LLM provider for better results."


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
