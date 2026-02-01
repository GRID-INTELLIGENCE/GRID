"""
Mistral AI Agent Service

Provides a safe interface to the Mistral AI API with python-dotenv for
secure API key loading from environment variables.

Usage:
    from grid.services.mistral_agent import MistralAgentService

    agent = MistralAgentService()
    response = agent.generate("What is the capital of France?")
"""

import os
from pathlib import Path
from typing import Any

# Load environment variables from .env file
from dotenv import load_dotenv

# Load from repo root .env if it exists
_repo_root = Path(__file__).resolve().parents[3]
_env_file = _repo_root / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
else:
    load_dotenv()  # Try default locations

# Import Mistral SDK (optional - only required when actually used)
_Mistral = None
_mistral_import_error: str | None = None

try:
    from mistralai import Mistral as _Mistral  # type: ignore[import-not-found]
except ImportError:
    _mistral_import_error = "mistralai package not installed. Run: pip install mistralai"


def _get_mistral_class():
    """Get the Mistral class, raising ImportError only when actually needed."""
    if _Mistral is None:
        raise ImportError(_mistral_import_error or "mistralai package not available")
    return _Mistral


class MistralAgentService:
    """
    Service for interacting with Mistral AI API.

    Uses python-dotenv for safe API key loading from environment variables.
    Supports both cloud API and local Ollama fallback.
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize the Mistral Agent Service.

        Args:
            api_key: Optional API key. If not provided, reads from MISTRAL_API_KEY env var.
        """
        self._api_key = api_key
        self._client = None  # Mistral client, lazy-loaded

        # Default configuration from environment
        self.default_model = os.getenv("MISTRAL_AGENT_MODEL", "mistral-large-latest")
        self.max_tokens = int(os.getenv("MISTRAL_MAX_TOKENS", "1024"))
        self.temperature = float(os.getenv("MISTRAL_TEMPERATURE", "0.7"))

    @property
    def client(self):
        """Lazy-loaded Mistral client."""
        if self._client is None:
            # Check if mistralai is available (raises ImportError if not)
            Mistral = _get_mistral_class()

            api_key = self._api_key or os.getenv("MISTRAL_API_KEY")
            if not api_key:
                raise ValueError(
                    "MISTRAL_API_KEY not set. Either:\n"
                    "1. Set MISTRAL_API_KEY environment variable\n"
                    "2. Create a .env file with MISTRAL_API_KEY=your_key\n"
                    "3. Pass api_key to MistralAgentService()"
                )
            self._client = Mistral(api_key=api_key)
        return self._client

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """
        Generate a response from Mistral AI.

        Args:
            prompt: User message/prompt
            model: Model to use (default: MISTRAL_AGENT_MODEL or mistral-large-latest)
            system_prompt: Optional system instruction
            max_tokens: Max tokens in response
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Generated text response
        """
        model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature

        messages: list[Any] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.complete(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if response and response.choices:
            return str(response.choices[0].message.content)
        return ""

    def generate_with_context(
        self,
        prompt: str,
        context: list[dict[str, str]],
        model: str | None = None,
    ) -> str:
        """
        Generate with conversation context.

        Args:
            prompt: Current user message
            context: Previous messages [{"role": "user/assistant", "content": "..."}]
            model: Model to use

        Returns:
            Generated response
        """
        model = model or self.default_model
        messages: list[Any] = context + [{"role": "user", "content": prompt}]

        response = self.client.chat.complete(
            model=model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        if response and response.choices:
            return str(response.choices[0].message.content)
        return ""

    def list_models(self) -> list[str]:
        """List available Mistral models."""
        # Common Mistral models as of 2025
        return [
            "mistral-large-latest",
            "mistral-medium-latest",
            "mistral-small-latest",
            "codestral-latest",
            "ministral-3b-latest",
            "ministral-8b-latest",
            "open-mistral-nemo",
        ]


# Convenience function
def get_mistral_agent(api_key: str | None = None) -> MistralAgentService:
    """Get a configured MistralAgentService instance."""
    return MistralAgentService(api_key=api_key)


if __name__ == "__main__":
    # Quick test
    print("Mistral Agent Service loaded.")
    print(f"Default model: {os.getenv('MISTRAL_AGENT_MODEL', 'mistral-large-latest')}")
    print(f"API key set: {'Yes' if os.getenv('MISTRAL_API_KEY') else 'No'}")
