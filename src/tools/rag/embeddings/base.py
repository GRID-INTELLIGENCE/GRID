"""Base embedding provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseEmbeddingProvider(ABC):
    """Base class for embedding providers.

    All embedding providers should return dense vectors (lists or numpy arrays),
    not sparse dictionaries, to preserve information and enable proper similarity search.
    """

    @abstractmethod
    def embed(self, text: str) -> list[float] | Any:
        """Generate embedding for text.

        Args:
            text: Input text to embed

        Returns:
            Dense embedding vector as list or numpy array
        """
        pass

    def embed_batch(self, texts: list[str]) -> list[list[float] | Any]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of dense embedding vectors
        """
        return [self.embed(text) for text in texts]

    @abstractmethod
    async def async_embed(self, text: str) -> list[float] | Any:
        """Generate embedding for text (async).

        Args:
            text: Input text to embed

        Returns:
            Dense embedding vector as list or numpy array
        """
        pass

    async def async_embed_batch(self, texts: list[str]) -> list[list[float] | Any]:
        """Generate embeddings for multiple texts (async).

        Args:
            texts: List of input texts

        Returns:
            List of dense embedding vectors
        """
        return [await self.async_embed(text) for text in texts]

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of embeddings produced by this provider."""
        pass
