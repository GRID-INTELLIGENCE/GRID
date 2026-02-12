"""
Test Embedding Provider for Unit Testing and Benchmarking.

Based on Smart Search concept from E:/grid/cognition/Time/l'instant/smart_search/.

IMPORTANT: This provider is for TESTING ONLY.
- Deterministic hash-based embeddings (NOT semantic)
- Semantically similar texts produce unrelated vectors
- Use only for mocking, benchmarking, or reproducible test fixtures
- DO NOT use for production RAG or real applications

Features:
- Deterministic: Same text always produces same vector
- Instant generation: No API calls or model downloads
- Small vectors: 384 dimensions (50% smaller than typical 768-dim)
- Zero external dependencies: Only numpy required

Performance:
- Embedding generation: <1ms (deterministic hash)
- Memory: Minimal (384-dim vectors)

Trade-offs:
- NO semantic understanding (vectors are random based on hash)
- Cannot perform actual semantic search
- Only useful for testing infrastructure
"""

from __future__ import annotations

import hashlib
import logging
from typing import cast

import numpy as np

from .base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


class TestEmbeddingProvider(BaseEmbeddingProvider):
    """
    Test embedding provider using deterministic hash-based embeddings.

    Based on Smart Search concept - deterministic but NON-SEMANTIC embeddings.

    WARNING: This provider produces deterministic random vectors, NOT semantic
    embeddings. Semantically similar texts (e.g., "machine learning" and
    "AI algorithms") will produce completely unrelated vectors due to different
    MD5 hashes.

    USE CASES:
    1. Unit testing (reproducible fixtures)
    2. Benchmarking (isolate performance from model inference)
    3. Integration testing (mock Ollama without external dependencies)

    DO NOT USE FOR:
    1. Production RAG (no semantic search capability)
    2. Real applications (no actual semantic understanding)
    """

    # Default dimension based on Smart Search concept
    DEFAULT_DIMENSION = 384  # 50% smaller than typical 768-dim

    def __init__(self, dimension: int = DEFAULT_DIMENSION):
        """Initialize test embedding provider.

        Args:
            dimension: Embedding dimension (default 384 from Smart Search)
        """
        self._dimension = dimension
        logger.warning(
            "TestEmbeddingProvider initialized. "
            "This produces NON-SEMANTIC embeddings for testing only."
        )

    def embed(self, text: str) -> list[float]:
        """Generate deterministic embedding for text.

        Uses MD5 hash → seed → random vector → L2 normalization.
        Same text always produces same vector, but semantically similar
        texts produce unrelated vectors.

        Args:
            text: Input text to embed

        Returns:
            Dense embedding vector as list of floats
        """
        if not text:
            return [0.0] * self._dimension

        # Create deterministic seed from text hash
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        seed = int(text_hash[:8], 16)

        # Generate deterministic random vector
        np.random.seed(seed)
        vector = np.random.randn(self._dimension).astype(np.float32)

        # Normalize to unit length (L2 normalization)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    async def async_embed(self, text: str) -> list[float]:
        """Generate embedding for text (async).

        Since this is deterministic and fast, just call the sync method.

        Args:
            text: Input text to embed

        Returns:
            Dense embedding vector as list of floats
        """
        return self.embed(text)

    @property
    def dimension(self) -> int:
        """Return the dimension of embeddings produced by this provider."""
        return self._dimension

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of dense embedding vectors
        """
        return cast(list[list[float]], [self.embed(text) for text in texts])

    async def async_embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts (async).

        Args:
            texts: List of input texts

        Returns:
            List of dense embedding vectors
        """
        return cast(list[list[float]], [await self.async_embed(text) for text in texts])

    def is_semantic(self) -> bool:
        """Return False since this is NOT a semantic embedding provider."""
        return False

    def get_info(self) -> dict[str, str]:
        """Get provider information.

        Returns:
            Dictionary with provider metadata
        """
        return {
            "provider": "TestEmbeddingProvider",
            "type": "deterministic_hash_based",
            "dimension": str(self._dimension),
            "semantic": "false",
            "use_case": "testing_mocking_benchmarking_only",
            "warning": "NON-SEMANTIC embeddings - do not use for production",
        }


# Global instance for convenience
_test_provider: TestEmbeddingProvider | None = None


def get_test_provider(dimension: int = TestEmbeddingProvider.DEFAULT_DIMENSION) -> TestEmbeddingProvider:
    """Get the global test embedding provider instance.

    Args:
        dimension: Embedding dimension (default 384 from Smart Search)

    Returns:
        Test embedding provider singleton
    """
    global _test_provider
    if _test_provider is None or _test_provider.dimension != dimension:
        _test_provider = TestEmbeddingProvider(dimension=dimension)
    return _test_provider
