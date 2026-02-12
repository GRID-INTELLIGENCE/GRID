"""OpenAI embedding provider."""

import os
from typing import cast

import numpy as np

from .base import BaseEmbeddingProvider


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
        timeout: int = 60,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "").strip()
        self.timeout = timeout
        self._dimension: int | None = None

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")

    def _client(self):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai is not installed. Install with: pip install openai") from None

        return OpenAI(api_key=self.api_key, timeout=self.timeout)

    def embed(self, text: str) -> list[float] | np.ndarray:
        client = self._client()
        resp = client.embeddings.create(model=self.model, input=text)
        vec = resp.data[0].embedding
        if self._dimension is None:
            self._dimension = len(vec)
        return cast(list[float] | np.ndarray, vec)

    def embed_batch(self, texts: list[str]) -> list[list[float] | np.ndarray]:
        if not texts:
            return []

        client = self._client()
        resp = client.embeddings.create(model=self.model, input=texts)
        vectors: list[list[float]] = [d.embedding for d in resp.data]
        if self._dimension is None and vectors:
            self._dimension = len(vectors[0])
        return cast(list[list[float] | np.ndarray], vectors)

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            try:
                self._dimension = len(cast(list[float], self.embed("test")))
            except Exception:
                # Default to common OpenAI embedding dimension for safety
                self._dimension = 1536
        return cast(int, self._dimension)
