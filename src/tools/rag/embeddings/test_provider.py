"""Test embedding provider for unit testing.

This provider generates deterministic embeddings based on input text,
making tests reproducible and independent of external services.

WARNING: This provider is NOT for production use. It generates embeddings
based on simple hashing and does not capture semantic meaning.
"""

from __future__ import annotations

import hashlib
from typing import ClassVar

import numpy as np

from .base import BaseEmbeddingProvider


class DeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic embedding provider for testing.

    Generates reproducible embeddings based on text hashing.
    Useful for unit tests where you need consistent results
    without external dependencies.

    Usage:
        provider = DeterministicEmbeddingProvider(dimension=384)
        embedding = provider.embed("test text")
        assert len(embedding) == 384

        # Same input always produces same output
        assert provider.embed("hello") == provider.embed("hello")
    """

    DEFAULT_DIMENSION: ClassVar[int] = 384

    def __init__(self, dimension: int = DEFAULT_DIMENSION, seed: int = 42):
        """Initialize test embedding provider.

        Args:
            dimension: Dimension of output embeddings (default: 384)
            seed: Random seed for reproducibility (default: 42)
        """
        self._dimension = dimension
        self._seed = seed
        self._cache: dict[str, list[float]] = {}

    @property
    def dimension(self) -> int:
        """Return the dimension of embeddings produced by this provider."""
        return self._dimension

    def _generate_deterministic_embedding(self, text: str) -> list[float]:
        """Generate a deterministic embedding from text.

        Uses SHA-256 hash of text to seed a random number generator,
        producing consistent embeddings for the same input.

        Args:
            text: Input text

        Returns:
            List of floats representing the embedding
        """
        # Check cache first
        if text in self._cache:
            return self._cache[text]

        # Create deterministic seed from text
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        # Combine with instance seed for flexibility
        combined_seed = int(text_hash[:8], 16) ^ self._seed

        # Generate deterministic random embedding
        rng = np.random.default_rng(combined_seed)  # type: ignore[attr-defined]
        embedding: np.ndarray = rng.standard_normal(self._dimension).astype(np.float32)  # type: ignore[assignment,union-attr]

        # Normalize to unit length (common for embeddings)
        norm: float = float(np.linalg.norm(embedding))  # type: ignore[arg-type]
        if norm > 0:
            embedding = embedding / norm

        result = embedding.tolist()
        self._cache[text] = result
        return result

    def embed(self, text: str) -> list[float]:
        """Generate embedding for text.

        Args:
            text: Input text to embed

        Returns:
            Dense embedding vector as list of floats
        """
        return self._generate_deterministic_embedding(text)

    async def async_embed(self, text: str) -> list[float]:
        """Generate embedding for text (async).

        Args:
            text: Input text to embed

        Returns:
            Dense embedding vector as list of floats
        """
        # Synchronous operation, but async interface for compatibility
        return self._generate_deterministic_embedding(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of dense embedding vectors
        """
        return [self.embed(text) for text in texts]

    async def async_embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts (async).

        Args:
            texts: List of input texts

        Returns:
            List of dense embedding vectors
        """
        return [await self.async_embed(text) for text in texts]

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()

    def similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts.

        Useful for testing similarity-based features.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Cosine similarity score between -1 and 1
        """
        emb1: np.ndarray = np.array(self.embed(text1))  # type: ignore[assignment]
        emb2: np.ndarray = np.array(self.embed(text2))  # type: ignore[assignment]

        dot_product: float = float(np.dot(emb1, emb2))  # type: ignore[arg-type]
        norm1: float = float(np.linalg.norm(emb1))  # type: ignore[arg-type]
        norm2: float = float(np.linalg.norm(emb2))  # type: ignore[arg-type]

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


# Singleton instance for convenience
_default_provider: DeterministicEmbeddingProvider | None = None


def get_test_provider(
    dimension: int = DeterministicEmbeddingProvider.DEFAULT_DIMENSION,
    seed: int = 42,
    singleton: bool = True,
) -> DeterministicEmbeddingProvider:
    """Get a test embedding provider.

    Args:
        dimension: Dimension of output embeddings
        seed: Random seed for reproducibility
        singleton: If True, return a shared instance (default: True)

    Returns:
        DeterministicEmbeddingProvider instance
    """
    global _default_provider

    if singleton:
        if _default_provider is None or _default_provider.dimension != dimension:
            _default_provider = DeterministicEmbeddingProvider(dimension=dimension, seed=seed)
        return _default_provider

    return DeterministicEmbeddingProvider(dimension=dimension, seed=seed)


# Backward compatibility alias
TestEmbeddingProvider = DeterministicEmbeddingProvider

__all__ = ["DeterministicEmbeddingProvider", "TestEmbeddingProvider", "get_test_provider"]
