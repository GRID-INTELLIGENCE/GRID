"""OpenAI embedding provider."""

from __future__ import annotations

import os
from typing import Any, cast

from .base import BaseEmbeddingProvider


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider using the OpenAI API."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
        timeout: int = 60,
    ):
        """Initialize OpenAI embedding provider.

        Args:
            model: OpenAI embedding model name
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            timeout: Request timeout in seconds
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "").strip()
        self.timeout = timeout
        self._dimension: int | None = None

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")

    def _client(self) -> Any:
        """Get OpenAI client (lazy initialization)."""
        try:
            from openai import OpenAI as OpenAIClient  # type: ignore[import-untyped]
        except ImportError:
            raise ImportError("openai is not installed. Install with: pip install openai") from None

        return OpenAIClient(api_key=self.api_key, timeout=self.timeout)

    def embed(self, text: str) -> list[float] | Any:
        """Generate embedding for text.

        Args:
            text: Input text to embed

        Returns:
            Dense embedding vector as list of floats
        """
        client = self._client()
        resp = client.embeddings.create(model=self.model, input=text)
        vec = resp.data[0].embedding
        if self._dimension is None:
            self._dimension = len(vec)
        return cast(list[float], vec)

    def embed_batch(self, texts: list[str]) -> list[list[float] | Any]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of dense embedding vectors
        """
        if not texts:
            return []

        client = self._client()
        resp = client.embeddings.create(model=self.model, input=texts)
        vectors: list[list[float]] = [d.embedding for d in resp.data]
        if self._dimension is None and vectors:
            self._dimension = len(vectors[0])
        return cast(list[list[float] | Any], vectors)

    async def async_embed(self, text: str) -> list[float] | Any:
        """Generate embedding for text (async).

        Note: OpenAI's client is sync, so we just call the sync method.
        For true async, consider using httpx or aiohttp directly.

        Args:
            text: Input text to embed

        Returns:
            Dense embedding vector as list of floats
        """
        return self.embed(text)

    async def async_embed_batch(self, texts: list[str]) -> list[list[float] | Any]:
        """Generate embeddings for multiple texts (async).

        Args:
            texts: List of input texts

        Returns:
            List of dense embedding vectors
        """
        return self.embed_batch(texts)

    @property
    def dimension(self) -> int:
        """Return the dimension of embeddings produced by this provider."""
        if self._dimension is None:
            try:
                self._dimension = len(cast(list[float], self.embed("test")))
            except Exception:
                # Default to common OpenAI embedding dimension for safety
                self._dimension = 1536
        return cast(int, self._dimension)
