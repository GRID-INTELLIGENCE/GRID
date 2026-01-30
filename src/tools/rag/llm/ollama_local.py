"""Local Ollama LLM provider."""

import json
from typing import Any, cast

import httpx

from .base import BaseLLMProvider


class OllamaLocalLLM(BaseLLMProvider):
    """Local Ollama LLM provider for gpt-oss-safeguard and ministral models.

    Uses proper Ollama HTTP API or Python package.
    """

    def __init__(self, model: str = "ministral", base_url: str = "http://localhost:11434", timeout: int = 120):
        """Initialize local Ollama LLM provider.

        Args:
            model: Model name (ministral, gpt-oss-safeguard, etc.)
            base_url: Ollama base URL
            timeout: Request timeout in seconds
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using Ollama API.

        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens (Ollama uses num_predict)
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        try:
            # Try using Ollama Python package first
            try:
                import ollama

                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})

                response = ollama.chat(
                    model=self.model,
                    messages=messages,
                    options={"temperature": temperature, "num_predict": max_tokens, **kwargs},
                )
                return cast(str, response["message"]["content"])
            except ImportError:
                # Fallback to HTTP API
                pass

            # Use HTTP API
            with httpx.Client(timeout=self.timeout) as client:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature, **kwargs},
                }

                if system:
                    payload["system"] = system

                if max_tokens:
                    payload["options"]["num_predict"] = max_tokens

                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.model_dump_json()
                return cast(str, data.get("response", ""))

        except Exception as e:
            raise RuntimeError(
                f"Failed to generate text from Ollama model {self.model}: {e}. "
                f"Make sure Ollama is running and the model is available: "
                f"ollama pull {self.model}"
            ) from e

    def stream(self, prompt: str, system: str | None = None, temperature: float = 0.7, **kwargs: Any) -> Any:
        """Stream text generation.

        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Yields:
            Text chunks as they are generated
        """
        try:
            # Try using Ollama Python package first
            try:
                import ollama

                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})

                stream = ollama.chat(
                    model=self.model, messages=messages, options={"temperature": temperature, **kwargs}, stream=True
                )

                for chunk in stream:
                    if "message" in chunk and "content" in chunk["message"]:
                        yield chunk["message"]["content"]
                return
            except ImportError:
                # Fallback to HTTP API
                pass

            # Use HTTP API streaming
            with httpx.Client(timeout=self.timeout) as client:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {"temperature": temperature, **kwargs},
                }

                if system:
                    payload["system"] = system

                with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            raise RuntimeError(f"Failed to stream text from Ollama model {self.model}: {e}") from e

    async def async_generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using native async Ollama client."""
        from grid.services.llm.llm_client import LLMConfig, LLMMessage, OllamaNativeClient

        messages = []
        if system:
            messages.append(LLMMessage(role="system", content=system))
        messages.append(LLMMessage(role="user", content=prompt))

        client = OllamaNativeClient(host=self.base_url)
        resp = await client.chat(
            messages=messages,
            config=LLMConfig(model=self.model, temperature=temperature, max_tokens=max_tokens or 2048),
        )
        return resp.content

    async def async_stream(
        self, prompt: str, system: str | None = None, temperature: float = 0.7, **kwargs: Any
    ) -> Any:
        """Stream text generation using native async Ollama client."""
        from grid.services.llm.llm_client import LLMConfig, OllamaNativeClient

        # OllamaNativeClient.stream currently only takes prompt, not messages
        # I might need to update LLMClient to support async_stream with messages
        client = OllamaNativeClient(host=self.base_url)

        # Simple implementation for now (using generate-style stream)
        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        async for chunk in client.stream(
            prompt=full_prompt, config=LLMConfig(model=self.model, temperature=temperature)
        ):
            yield chunk
