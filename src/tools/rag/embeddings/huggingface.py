"""Hugging Face embedding provider using sentence-transformers."""

from typing import cast

import numpy as np

from .base import BaseEmbeddingProvider


class HuggingFaceEmbeddingProvider(BaseEmbeddingProvider):
    """Hugging Face embedding provider using sentence-transformers library.

    This provider runs locally using the sentence-transformers package.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", device: str = "cpu"):
        """Initialize Hugging Face provider.

        Args:
            model_name: Hugging Face model identifier
            device: Device to run on ('cpu', 'cuda', etc.)
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. Please install with: pip install sentence-transformers"
            ) from None

        self.model_name = model_name
        self.device = device
        self._model = SentenceTransformer(model_name, device=device)
        self._dimension = self._model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> list[float] | np.ndarray:
        """Generate embedding for text.

        Args:
            text: Input text to embed

        Returns:
            Dense embedding vector
        """
        return cast(list[float] | np.ndarray, self._model.encode(text, convert_to_numpy=True))

    def embed_batch(self, texts: list[str]) -> list[list[float] | np.ndarray]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of dense embedding vectors
        """
        return cast(list[list[float] | np.ndarray], self._model.encode(texts, convert_to_numpy=True))

    async def async_embed(self, text: str) -> list[float] | np.ndarray:
        """Generate embedding for text (async)."""
        import asyncio

        return await asyncio.to_thread(self.embed, text)

    async def async_embed_batch(self, texts: list[str]) -> list[list[float] | np.ndarray]:
        """Generate embeddings for multiple texts (async)."""
        import asyncio

        return await asyncio.to_thread(self.embed_batch, texts)

    @property
    def dimension(self) -> int:
        """Return the dimension of embeddings produced by this provider."""
        return cast(int, self._dimension)
