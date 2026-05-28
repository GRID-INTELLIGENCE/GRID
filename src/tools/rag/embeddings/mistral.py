"""Mistral AI embedding provider."""

from __future__ import annotations

import logging
import os
from typing import Any, cast

from tools.rag.resilience import get_circuit_breaker

from .base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


class MistralEmbeddingProvider(BaseEmbeddingProvider):
    """Mistral AI embedding provider using the mistral-embed model."""

    def __init__(
        self,
        model: str = "mistral-embed",
        api_key: str | None = None,
        timeout: int = 60,
    ):
        """Initialize Mistral embedding provider.

        Args:
            model: Mistral embedding model name (mistral-embed)
            api_key: Mistral API key (defaults to MISTRAL_API_KEY env var)
            timeout: Request timeout in seconds
        """
        self.model = model
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY", "").strip()
        self.timeout = timeout
        self._dimension: int | None = None
        self._client_instance: Any = None
        self._breaker = get_circuit_breaker("mistral")

        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY is required for Mistral embeddings")

    def _client(self) -> Any:
        """Get Mistral client (lazy initialization)."""
        if self._client_instance is None:
            try:
                from mistralai import Mistral
            except ImportError:
                raise ImportError("mistralai is not installed. Install with: pip install mistralai") from None
            self._client_instance = Mistral(api_key=self.api_key)
        return self._client_instance

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        client = self._client()
        with self._breaker:
            resp = client.embeddings.create(model=self.model, inputs=[text])
        vec = cast(list[float], resp.data[0].embedding)
        if self._dimension is None:
            self._dimension = len(vec)
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []
        client = self._client()
        with self._breaker:
            resp = client.embeddings.create(model=self.model, inputs=texts)
        vectors = [cast(list[float], d.embedding) for d in resp.data]
        if self._dimension is None and vectors:
            self._dimension = len(vectors[0])
        return vectors

    async def async_embed(self, text: str) -> list[float]:
        """Generate embedding for a single text (async delegates to sync)."""
        return self.embed(text)

    async def async_embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts (async delegates to sync)."""
        return self.embed_batch(texts)

    @property
    def dimension(self) -> int:
        """Return the dimension of embeddings (1024 for mistral-embed)."""
        if self._dimension is None:
            try:
                self._dimension = len(self.embed("test"))
            except Exception:
                self._dimension = 1024  # mistral-embed produces 1024-dim vectors
        return self._dimension
