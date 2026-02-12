"""Nomic Embed Text V2 embedding provider using Ollama."""

from typing import cast

import httpx
import numpy as np

from .base import BaseEmbeddingProvider


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """Ollama-based embedding provider supporting various models (Nomic V1, V2, etc.).

    Uses proper Ollama HTTP API or Python package to get embeddings.
    Returns dense vectors (not sparse dicts) for proper similarity search.
    """

    def __init__(
        self, model: str = "nomic-embed-text-v2-moe:latest", base_url: str = "http://localhost:11434", timeout: int = 30
    ):
        """Initialize Nomic Embedding V2 provider.

        Args:
            model: Model name (default: nomic-embed-text-v2-moe:latest)
            base_url: Ollama base URL (default: http://localhost:11434)
            timeout: Request timeout in seconds
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._dimension: int | None = None
        self.max_text_length = 6000  # Conservative limit for nomic models (~8192 tokens)

    def _truncate_text(self, text: str, max_chars: int | None = None) -> str:
        """Truncate text to fit within model's context window.

        Args:
            text: Input text
            max_chars: Maximum characters (default: self.max_text_length)

        Returns:
            Truncated text
        """
        if max_chars is None:
            max_chars = self.max_text_length

        if len(text) <= max_chars:
            return text

        # Truncate and add indicator
        truncated = text[: max_chars - 50]  # Leave room for truncation message
        return truncated + "\n\n[Text truncated due to length limit]"

    def embed(self, text: str) -> list[float]:
        """Generate embedding using Ollama API.

        Args:
            text: Input text to embed

        Returns:
            Dense embedding vector as list of floats
        """
        # Truncate text if too long (safety measure)
        original_length = len(text)
        text = self._truncate_text(text)
        if len(text) < original_length:
            pass  # print(f"Warning: Text truncated from {original_length} to {len(text)} characters")

        # STRICT MODE: Only use the configured model. No fallbacks.
        models_to_try = [self.model]

        last_error = None

        for model_name in models_to_try:
            try:
                # Try using Ollama Python package first
                try:
                    import ollama

                    # DEBUG: Print what we are attempting
                    # print(f"DEBUG: Attempting ollama.embeddings with {model_name}")
                    response = ollama.embeddings(model=model_name, prompt=text)

                    # Handle both dict response and EmbeddingsResponse object
                    if hasattr(response, "embedding"):
                        embedding = response.embedding
                    else:
                        embedding = response.get("embedding", [])

                    # DEBUG: Print result status
                    # if not embedding:
                    #     print(f"DEBUG: Embedding is empty/None for {model_name}. Response keys/attrs: {dir(response)}")

                    if embedding:
                        if model_name != self.model:
                            print(f"Info: Using model '{model_name}' instead of '{self.model}'")
                        self._dimension = len(embedding)
                        self.model = model_name  # Update to working model
                        return cast(list[float], embedding)
                except ImportError:
                    # Fallback to HTTP API
                    pass
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()

                    # Check if it's a context length error
                    if "context length" in error_str or "exceeds" in error_str or "500" in error_str:
                        # Text is too long for this model, try significantly shorter
                        if len(text) > 4000:
                            text = self._truncate_text(text, max_chars=4000)
                            # We can recursion once to avoid complex loop logic
                            try:
                                return self.embed(text)
                            except Exception as inner_e:
                                last_error = inner_e
                                # continue to try next model or fail

                    # Check if it's a model not found error
                    if "not found" in error_str or "404" in error_str:
                        continue  # Try next model

                    # For other errors, continue to next model if available
                    continue

                # Use HTTP API
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.base_url}/api/embeddings", json={"model": model_name, "prompt": text}
                    )
                    if response.status_code == 404:
                        last_error = Exception(f"Model '{model_name}' not found (404)")
                        continue  # Try next model
                    if response.status_code == 500:
                        # Check if it's a context length error
                        error_text = response.text.lower() if hasattr(response, "text") else ""
                        if any(m in error_text for m in ["context length", "exceeds", "too long", "too large"]):
                            # Aggressively truncate and retry
                            text = self._truncate_text(text, max_chars=min(len(text) // 2, 4000))
                            if len(text) < 20:
                                return [0.0] * (self._dimension or 768)
                            continue  # Retry with shorter text

                    response.raise_for_status()
                    data = response.json()

                    # Handle different Ollama API response formats (embedding vs embeddings)
                    embedding = data.get("embedding")
                    if not embedding and "embeddings" in data:
                        embs = data.get("embeddings", [])
                        if embs and isinstance(embs, list):
                            embedding = embs[0]

                    if not embedding:
                        # Handle empty or whitespace strings gracefully
                        if not text.strip():
                            return [0.0] * (self._dimension or 768)
                        raise ValueError(f"No embedding returned from Ollama for model {model_name}. Response: {data}")

                    if model_name != self.model:
                        print(f"Info: Using model '{model_name}' instead of '{self.model}'")
                    self._dimension = len(embedding)
                    self.model = model_name  # Update to working model
                    return cast(list[float], embedding)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    last_error = e
                    continue  # Try next model
                if e.response.status_code == 500:
                    # Check if it's a context length error
                    error_text = e.response.text.lower() if hasattr(e.response, "text") else str(e).lower()
                    if "context length" in error_text or "exceeds" in error_text:
                        # Text is still too long, try shorter
                        text = self._truncate_text(text, max_chars=4000)
                        continue  # Retry with shorter text
                raise  # Re-raise for other HTTP errors
            except Exception as e:
                # Check if it's a context length error
                error_str = str(e).lower()
                if "context length" in error_str or "exceeds" in error_str:
                    # Text is still too long, try shorter
                    text = self._truncate_text(text, max_chars=4000)
                    continue  # Retry with shorter text
                # If it's not a "not found" or context length error, raise immediately
                if "not found" not in error_str and "404" not in error_str:
                    raise
                last_error = e
                continue

        # If we get here, all models failed
        error_msg = str(last_error) if last_error else "Unknown error"
        raise RuntimeError(
            f"Failed to get embedding from Ollama. Tried models: {', '.join(models_to_try)}\n"
            f"Error: {error_msg}\n\n"
            f"To fix this, run one of these commands:\n"
            f"  ollama pull nomic-embed-text-v2-moe:latest\n"
            f"  OR\n"
            f"  ollama pull nomic-embed-text-v2\n"
            f"  OR\n"
            f"  ollama pull nomic-embed-text\n\n"
            f"Then verify with: ollama list"
        ) from last_error

    async def async_embed(self, text: str) -> list[float]:
        """Generate embedding using native async Ollama client."""
        from grid.services.embeddings.embedding_client import OllamaEmbeddingClient

        text = self._truncate_text(text)
        client = OllamaEmbeddingClient(host=self.base_url)
        resp = await client.embed([text], model=self.model)
        if not resp.embeddings:
            raise RuntimeError(f"No embedding returned from native client for model {self.model}")
        embedding = resp.embeddings[0]
        self._dimension = len(embedding)
        return cast(list[float], embedding)

    async def async_embed_batch(self, texts: list[str]) -> list[list[float] | np.ndarray]:
        """Generate embeddings for multiple texts using native async batch API."""
        from grid.services.embeddings.embedding_client import OllamaEmbeddingClient

        truncated_texts = [self._truncate_text(t) for t in texts]
        client = OllamaEmbeddingClient(host=self.base_url)
        resp = await client.embed(truncated_texts, model=self.model)
        if len(resp.embeddings) != len(texts):
            return await super().async_embed_batch(texts)
        if resp.embeddings:
            self._dimension = len(resp.embeddings[0])
        return cast(list[list[float] | np.ndarray], resp.embeddings)

    def embed_batch(self, texts: list[str]) -> list[list[float] | np.ndarray]:
        """Generate embeddings for multiple texts using batch API if available.

        Args:
            texts: List of input texts

        Returns:
            List of dense embedding vectors
        """
        # but we can optimize with async if needed later
        results = [self.embed(text) for text in texts]
        return cast(list[list[float] | np.ndarray], results)

    @property
    def dimension(self) -> int:
        """Return the dimension of embeddings.

        Returns:
            Embedding dimension (768 for nomic-embed-text-v2)
        """
        if self._dimension is None:
            # Try to get dimension by embedding a small text
            try:
                test_embedding = self.embed("test")
                self._dimension = len(test_embedding)
            except Exception:
                # Default dimension for nomic-embed-text-v2
                self._dimension = 768
        return self._dimension
