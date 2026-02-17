"""
Comprehensive embedding provider tests for consistency, quality, and performance.
Tests all embedding providers: HuggingFace, Nomic, OpenAI, and Ollama.

Note: Requires sklearn for cosine similarity calculations.
Tests are skipped if sklearn is not available.
"""

from __future__ import annotations

import time

import numpy as np
import pytest

# Skip entire module if sklearn is not available
try:
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    pytest.skip(
        "sklearn not available - skipping embedding provider tests",
        allow_module_level=True,
    )

from tools.rag.embeddings.huggingface import HuggingFaceEmbeddingProvider
from tools.rag.embeddings.nomic_v2 import OllamaEmbeddingProvider
from tools.rag.embeddings.openai import OpenAIEmbeddingProvider
from tools.rag.embeddings.simple import SimpleEmbedding
from tools.rag.vector_store.in_memory_dense import InMemoryDenseVectorStore


class TestEmbeddingProviders:
    """Test all embedding providers for consistency and quality"""

    @pytest.fixture(params=["huggingface", "nomic", "simple"])
    def embedding_provider(self, request):
        """Parameterized fixture for testing embedding providers"""
        if request.param == "huggingface":
            return HuggingFaceEmbeddingProvider(model_name="sentence-transformers/all-MiniLM-L6-v2")
        elif request.param == "nomic":
            # Skip if Ollama is not available
            try:
                provider = OllamaEmbeddingProvider()
                # Try a quick test to see if Ollama is responding
                provider.embed("test")
                return provider
            except Exception as e:
                pytest.skip(f"Ollama not available: {e}")
        elif request.param == "simple":
            return SimpleEmbedding()
        else:
            pytest.fail(f"Unknown provider: {request.param}")

    @pytest.fixture
    def openai_provider(self):
        """OpenAI provider requires API key - skip if not available"""
        try:
            return OpenAIEmbeddingProvider(model="text-embedding-ada-002")
        except Exception:
            pytest.skip("OpenAI API key not available")

    def test_embedding_dimension_consistency(self, embedding_provider):
        """Scenario: All embeddings should have consistent dimensions for a provider"""
        texts = [
            "Short text",
            "This is a medium length text with multiple sentences and some complexity.",
            "This is a very long text that contains multiple paragraphs, various punctuation marks, numbers like 123, and special characters like @#$% to test how well embedding provider handles diverse content.",
        ]

        embeddings = embedding_provider.embed_batch(texts)

        # All embeddings should have same dimension
        dims = [len(embedding) for embedding in embeddings]
        assert len(set(dims)) == 1, f"Inconsistent dimensions: {dims}"

        # Dimension should be reasonable
        # Note: SimpleEmbedding is a fallback with lower dimensions (default 100)
        dim = dims[0]
        provider_name = type(embedding_provider).__name__
        if provider_name == "SimpleEmbedding":
            assert 50 <= dim <= 512, f"SimpleEmbedding dimension {dim} seems unreasonable"
        else:
            assert 256 <= dim <= 1536, f"Embedding dimension {dim} seems unreasonable"

        # Embeddings should be normalized (if provider does normalization)
        # Note: SimpleEmbedding is a fallback and doesn't normalize
        if provider_name != "SimpleEmbedding":
            for i, embedding in enumerate(embeddings):
                norm = float(np.linalg.norm(embedding))  # type: ignore[arg-type]
                if norm > 0:  # Skip zero vectors
                    assert 0.5 <= norm <= 2.0, f"Embedding {i} not normalized: {norm}"

    def test_single_vs_batch_consistency(self, embedding_provider):
        """Scenario: Single embedding should match batch embedding"""
        text = "This is a test sentence for embedding consistency check."

        # Single embedding
        single_embedding = embedding_provider.embed(text)

        # Batch embedding
        batch_embeddings = embedding_provider.embed_batch([text])
        batch_embedding = batch_embeddings[0]

        # Should be nearly identical
        similarity = cosine_similarity([single_embedding], [batch_embedding])[0][0]
        assert similarity > 0.999, f"Single vs batch similarity too low: {similarity}"

        # Same dimensions
        assert len(single_embedding) == len(batch_embedding), "Single and batch embeddings should have same dimensions"

    def test_embedding_quality_semantic_similarity(self, embedding_provider):
        """Scenario: Test semantic similarity of embeddings"""
        # Skip for SimpleEmbedding - it's a basic fallback without semantic understanding
        provider_name = type(embedding_provider).__name__
        if provider_name == "SimpleEmbedding":
            pytest.skip("SimpleEmbedding is a fallback without semantic understanding")

        # Similar concepts pairs
        similar_pairs = [
            ("machine learning", "artificial intelligence"),
            ("database", "data storage"),
            ("web development", "frontend programming"),
            ("financial report", "earnings statement"),
            ("medical diagnosis", "health assessment"),
        ]

        # Dissimilar concept pairs
        dissimilar_pairs = [
            ("machine learning", "cooking recipes"),
            ("database", "mountain climbing"),
            ("web development", "classical music"),
            ("financial report", "space exploration"),
            ("medical diagnosis", "sports analytics"),
        ]

        # Calculate similarities
        similar_scores = []
        dissimilar_scores = []

        for text1, text2 in similar_pairs:
            emb1, emb2 = embedding_provider.embed_batch([text1, text2])
            similarity = cosine_similarity([emb1], [emb2])[0][0]
            similar_scores.append(similarity)

        for text1, text2 in dissimilar_pairs:
            emb1, emb2 = embedding_provider.embed_batch([text1, text2])
            similarity = cosine_similarity([emb1], [emb2])[0][0]
            dissimilar_scores.append(similarity)

        # Semantic similarity should be higher for similar concepts
        avg_similar = float(np.mean(similar_scores))  # type: ignore[arg-type]
        avg_dissimilar = float(np.mean(dissimilar_scores))  # type: ignore[arg-type]

        assert (
            avg_similar > avg_dissimilar + 0.2
        ), f"Similar concepts (avg: {avg_similar:.3f}) should be more similar than dissimilar (avg: {avg_dissimilar:.3f})"

    def test_embedding_performance(self, embedding_provider):
        """Scenario: Test embedding generation performance"""
        # Test batch of 100 texts
        texts = [f"This is test document {i} with some content." for i in range(100)]

        start_time = time.time()
        embeddings = embedding_provider.embed_batch(texts)
        duration = time.time() - start_time

        # Performance assertions
        assert len(embeddings) == 100, "Should generate 100 embeddings"

        embeddings_per_second = len(texts) / duration
        assert embeddings_per_second > 10, f"Embedding too slow: {embeddings_per_second:.1f} docs/sec, expected >10"

        # Memory efficiency
        total_size = sum(len(emb) for emb in embeddings)
        assert total_size == 100 * len(embeddings[0]), "All embeddings should have same size"


class TestEmbeddingQuality:
    """Advanced tests for embedding quality and characteristics"""

    def test_embedding_distribution_properties(self):
        """Test statistical properties of embeddings"""
        # Use HuggingFace provider for quality tests - SimpleEmbedding is just a fallback
        provider = HuggingFaceEmbeddingProvider(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # Generate embeddings for diverse text (100 unique texts)
        texts = []
        for i in range(100):
            topic = i % 5
            if topic == 0:
                texts.append(
                    f"Topic {i}: This is a sample text about different subjects and concepts with unique identifier {i}"
                )
            elif topic == 1:
                texts.append(f"Science {i}: Technology innovation and research methodology with unique identifier {i}")
            elif topic == 2:
                texts.append(f"Arts {i}: Creative expression and cultural heritage with unique identifier {i}")
            elif topic == 3:
                texts.append(f"Sports {i}: Athletic performance and competitive events with unique identifier {i}")
            else:
                texts.append(f"Business {i}: Economic analysis and market trends with unique identifier {i}")

        embeddings = provider.embed_batch(texts)
        embedding_matrix: np.ndarray = np.array(embeddings)  # type: ignore[assignment]

        # Statistical properties
        mean_embedding: np.ndarray = np.mean(embedding_matrix, axis=0)  # type: ignore[assignment]
        std_embedding: np.ndarray = np.std(embedding_matrix, axis=0)  # type: ignore[assignment]

        # Mean should be reasonably close to 0 for normalized embeddings
        # Note: sentence-transformers models may have slight bias, so we use a relaxed threshold
        assert np.all(np.abs(mean_embedding) < 0.15), (  # type: ignore[arg-type]
            f"Embedding mean should be near zero, got max abs: {float(np.max(np.abs(mean_embedding))):.3f}"  # type: ignore[arg-type]
        )

        # Standard deviation should be reasonable - use more diverse texts to ensure variance
        assert float(np.mean(std_embedding)) > 0.01, "Embeddings should have some variance"  # type: ignore[arg-type]
        assert np.all(std_embedding < 1.0), "Embeddings should not have excessive variance"  # type: ignore[arg-type]

    def test_embedding_uniqueness(self):
        """Test that different texts produce different embeddings"""
        # Use HuggingFace provider for quality tests - SimpleEmbedding is just a fallback
        provider = HuggingFaceEmbeddingProvider(model_name="sentence-transformers/all-MiniLM-L6-v2")

        texts = [f"Unique text number {i} with specific content {i * 10}" for i in range(50)]

        embeddings = provider.embed_batch(texts)

        # All embeddings should be unique
        similarities = cosine_similarity(embeddings)
        np.fill_diagonal(similarities, -1)  # type: ignore[arg-type]  # Ignore self-similarity

        max_similarity = float(np.max(similarities))  # type: ignore[arg-type]
        assert max_similarity < 0.95, f"Embeddings should be unique, max similarity: {max_similarity:.3f}"

    def test_embedding_reproducibility(self):
        """Test that same input produces same output"""
        # Use HuggingFace provider for quality tests - SimpleEmbedding is just a fallback
        provider = HuggingFaceEmbeddingProvider(model_name="sentence-transformers/all-MiniLM-L6-v2")

        text = "This is a reproducibility test."

        # Generate embedding twice
        emb1 = provider.embed(text)
        emb2 = provider.embed(text)

        # Should be identical
        similarity = cosine_similarity([emb1], [emb2])[0][0]
        assert similarity > 0.9999, f"Embeddings should be reproducible, similarity: {similarity:.6f}"

        # Batch should also be reproducible
        batch1 = provider.embed_batch([text])
        batch2 = provider.embed_batch([text])

        batch_similarity = cosine_similarity([batch1[0]], [batch2[0]])[0][0]
        assert batch_similarity > 0.9999, f"Batch embeddings should be reproducible, similarity: {batch_similarity:.6f}"


class TestEmbeddingIntegration:
    """Integration tests with vector stores and RAG pipeline"""

    def test_embedding_vector_store_integration(self):
        """Test embeddings work correctly with vector stores"""
        # Use HuggingFace provider for integration tests - SimpleEmbedding is just a fallback
        provider = HuggingFaceEmbeddingProvider(model_name="sentence-transformers/all-MiniLM-L6-v2")
        store = InMemoryDenseVectorStore()

        documents = [
            {"content": "Machine learning algorithms", "metadata": {"topic": "AI"}},
            {"content": "Traditional cooking recipes", "metadata": {"topic": "cooking"}},
            {"content": "Deep learning models", "metadata": {"topic": "AI"}},
        ]

        # Add documents (should use embeddings internally)
        # First generate embeddings for the documents
        from tools.rag.types import Document

        doc_objects = [
            Document(text=doc["content"], metadata=doc["metadata"], id=f"doc_{i}") for i, doc in enumerate(documents)
        ]

        # Generate embeddings for documents
        batch_embeddings = provider.embed_batch([doc.text for doc in doc_objects])
        # Convert to list format if needed
        embeddings = [emb.tolist() if hasattr(emb, "tolist") else list(emb) for emb in batch_embeddings]  # type: ignore[union-attr]
        ids = [doc.id for doc in doc_objects]
        documents_list = [doc.text for doc in doc_objects]
        metadatas = [doc.metadata for doc in doc_objects]

        store.add(ids=ids, documents=documents_list, embeddings=embeddings, metadatas=metadatas)

        # Search should work (need to generate embedding for query first)
        query_embedding_raw = provider.embed("neural networks")
        # Convert to list if numpy array
        query_embedding: list[float] = (
            query_embedding_raw.tolist() if hasattr(query_embedding_raw, "tolist") else list(query_embedding_raw)  # type: ignore[union-attr]
        )
        results = store.query(query_embedding=query_embedding, n_results=2)

        # Results is a dict with keys: ids, documents, metadatas, distances
        assert len(results["ids"]) == 2, f"Should return 2 results, got {len(results['ids'])}"

        # AI documents should rank higher
        topics = [meta.get("topic") for meta in results["metadatas"]]
        assert topics[0] == "AI", f"First result should be AI, got {topics[0]}"
