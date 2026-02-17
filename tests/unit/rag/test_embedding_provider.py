"""Unit tests for TestEmbeddingProvider.

Tests verify the deterministic embedding provider produces consistent,
reproducible embeddings suitable for testing purposes.
"""

import numpy as np
import pytest

from tools.rag.embeddings.test_provider import DeterministicEmbeddingProvider, get_test_provider


class TestDeterministicEmbeddingProviderInit:
    """Tests for DeterministicEmbeddingProvider initialization."""

    def test_default_dimension(self):
        """Test default dimension is 384."""
        provider = DeterministicEmbeddingProvider()
        assert provider.dimension == 384

    def test_custom_dimension(self):
        """Test custom dimension can be set."""
        provider = DeterministicEmbeddingProvider(dimension=768)
        assert provider.dimension == 768

    def test_custom_seed(self):
        """Test custom seed can be set."""
        provider1 = DeterministicEmbeddingProvider(seed=42)
        provider2 = DeterministicEmbeddingProvider(seed=123)

        # Different seeds should produce different embeddings for same text
        emb1 = provider1.embed("test")
        emb2 = provider2.embed("test")

        assert emb1 != emb2


class TestDeterministicEmbeddingProviderEmbed:
    """Tests for embedding generation."""

    @pytest.fixture
    def provider(self):
        """Create a test provider instance."""
        return DeterministicEmbeddingProvider(dimension=384, seed=42)

    def test_embed_returns_correct_dimension(self, provider):
        """Test that embed returns vector of correct dimension."""
        embedding = provider.embed("hello world")
        assert len(embedding) == 384

    def test_embed_returns_list_of_floats(self, provider):
        """Test that embed returns a list of floats."""
        embedding = provider.embed("test text")
        assert isinstance(embedding, list)
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_is_deterministic(self, provider):
        """Test that same input produces same output."""
        text = "deterministic test"
        emb1 = provider.embed(text)
        emb2 = provider.embed(text)
        assert emb1 == emb2

    def test_embed_different_texts_different_embeddings(self, provider):
        """Test that different texts produce different embeddings."""
        emb1 = provider.embed("first text")
        emb2 = provider.embed("second text")
        assert emb1 != emb2

    def test_embed_is_normalized(self, provider):
        """Test that embeddings are normalized to unit length."""
        embedding = provider.embed("normalize test")
        norm = float(np.linalg.norm(embedding))  # type: ignore[arg-type]
        assert abs(norm - 1.0) < 1e-5, f"Expected unit norm, got {norm}"

    def test_embed_empty_string(self, provider):
        """Test embedding of empty string."""
        # Should not raise, may return zero vector or hash-based vector
        embedding = provider.embed("")
        assert len(embedding) == 384

    def test_embed_unicode(self, provider):
        """Test embedding of unicode text."""
        embedding = provider.embed("Hello 世界 🌍")
        assert len(embedding) == 384


class TestDeterministicEmbeddingProviderBatch:
    """Tests for batch embedding generation."""

    @pytest.fixture
    def provider(self):
        """Create a test provider instance."""
        return DeterministicEmbeddingProvider(dimension=384, seed=42)

    def test_embed_batch_returns_list(self, provider):
        """Test that embed_batch returns a list of embeddings."""
        texts = ["text one", "text two", "text three"]
        embeddings = provider.embed_batch(texts)

        assert isinstance(embeddings, list)
        assert len(embeddings) == 3

    def test_embed_batch_correct_dimensions(self, provider):
        """Test that each embedding in batch has correct dimension."""
        texts = ["a", "b", "c"]
        embeddings = provider.embed_batch(texts)

        for emb in embeddings:
            assert len(emb) == 384

    def test_embed_batch_matches_individual(self, provider):
        """Test that batch embedding matches individual embedding."""
        texts = ["first", "second"]
        batch_result = provider.embed_batch(texts)

        individual_results = [provider.embed(t) for t in texts]

        assert batch_result == individual_results

    def test_embed_batch_empty_list(self, provider):
        """Test embedding of empty list."""
        embeddings = provider.embed_batch([])
        assert embeddings == []


@pytest.mark.asyncio
class TestDeterministicEmbeddingProviderAsync:
    """Tests for async embedding methods."""

    @pytest.fixture
    def provider(self):
        """Create a test provider instance."""
        return DeterministicEmbeddingProvider(dimension=384, seed=42)

    async def test_async_embed(self, provider):
        """Test async embedding method."""
        embedding = await provider.async_embed("async test")
        assert len(embedding) == 384

    async def test_async_embed_matches_sync(self, provider):
        """Test that async and sync produce same results."""
        text = "consistency test"
        sync_result = provider.embed(text)
        async_result = await provider.async_embed(text)
        assert sync_result == async_result

    async def test_async_embed_batch(self, provider):
        """Test async batch embedding method."""
        texts = ["one", "two", "three"]
        embeddings = await provider.async_embed_batch(texts)

        assert len(embeddings) == 3
        for emb in embeddings:
            assert len(emb) == 384


class TestDeterministicEmbeddingProviderSimilarity:
    """Tests for similarity calculation."""

    @pytest.fixture
    def provider(self):
        """Create a test provider instance."""
        return DeterministicEmbeddingProvider(dimension=384, seed=42)

    def test_similarity_same_text_is_one(self, provider):
        """Test that similarity of same text is 1.0."""
        similarity = provider.similarity("identical", "identical")
        assert abs(similarity - 1.0) < 1e-5

    def test_similarity_range(self, provider):
        """Test that similarity is in valid range [-1, 1]."""
        similarity = provider.similarity("text one", "text two")
        assert -1.0 <= similarity <= 1.0


class TestGetTestProvider:
    """Tests for the get_test_provider factory function."""

    def test_returns_provider(self):
        """Test that factory returns a DeterministicEmbeddingProvider."""
        provider = get_test_provider()
        assert isinstance(provider, DeterministicEmbeddingProvider)

    def test_singleton_behavior(self):
        """Test that factory returns same instance (singleton)."""
        provider1 = get_test_provider()
        provider2 = get_test_provider()
        assert provider1 is provider2

    def test_different_dimension_creates_new(self):
        """Test that different dimension creates new instance."""
        provider1 = get_test_provider(dimension=384)
        provider2 = get_test_provider(dimension=768)
        assert provider1.dimension != provider2.dimension

    def test_non_singleton_mode(self):
        """Test that singleton=False creates new instance."""
        provider1 = get_test_provider(singleton=False)
        provider2 = get_test_provider(singleton=False)
        assert provider1 is not provider2


class TestCacheManagement:
    """Tests for embedding cache management."""

    def test_cache_stores_embeddings(self):
        """Test that embeddings are cached."""
        provider = DeterministicEmbeddingProvider()
        text = "cache test"

        # First call
        provider.embed(text)
        assert text in provider._cache

    def test_clear_cache(self):
        """Test that clear_cache removes all cached embeddings."""
        provider = DeterministicEmbeddingProvider()
        provider.embed("text1")
        provider.embed("text2")

        assert len(provider._cache) == 2

        provider.clear_cache()
        assert len(provider._cache) == 0
