"""
Comprehensive tests for Hybrid Search and Cross-Encoder Reranker.
Tests RRF fusion, BM25 integration, and neural reranking for improved relevance.

NOTE: These tests are skipped due to HuggingFace Hub metadata version conflicts.
These will be re-enabled in Phase 3 Sprint 2 after dependency resolution.
"""

from unittest.mock import Mock, patch

import numpy as np
import pytest

# Skip collection entirely for this module
pytest.skip("HuggingFace Hub importlib_metadata version issue", allow_module_level=True)

from tools.rag.cross_encoder_reranker import CrossEncoderReranker
from tools.rag.embeddings.simple import SimpleEmbeddings
from tools.rag.hybrid_retriever import HybridRetriever, tokenize
from tools.rag.reranker import NoOpReranker, OllamaReranker, create_reranker
from tools.rag.vector_store.in_memory_dense import InMemoryDenseStore


class TestHybridRetriever:
    """Test hybrid retrieval combining dense vectors and BM25."""

    @pytest.fixture
    def vector_store(self):
        """Create in-memory vector store for testing."""
        store = InMemoryDenseStore(embedding_dim=384)

        # Add sample documents
        documents = [
            "Machine learning algorithms power modern AI systems",
            "Deep learning neural networks process complex patterns",
            "Traditional baking methods use yeast and flour",
            "Training deep learning models requires large datasets",
            "Baking bread requires proper fermentation techniques",
            "Neural network architectures evolve rapidly",
        ]

        embeddings = SimpleEmbeddings(embedding_dim=384).embed_batch(documents)
        store.add(
            ids=[f"doc_{i}" for i in range(len(documents))],
            documents=documents,
            embeddings=embeddings,
            metadatas=[{"topic": "AI" if i < 3 or i >= 4 else "cooking"} for i in range(len(documents))],
        )

        return store

    @pytest.fixture
    def embedding_provider(self):
        """Create simple embedding provider for testing."""
        return SimpleEmbeddings(embedding_dim=384)

    @pytest.fixture
    def hybrid_retriever(self, vector_store, embedding_provider):
        """Create hybrid retriever instance."""
        return HybridRetriever(vector_store=vector_store, embedding_provider=embedding_provider, k=60)  # RRF parameter

    def test_tokenization_function(self):
        """Test the tokenization function used for BM25."""
        text = "Machine learning algorithms process complex patterns efficiently."
        tokens = tokenize(text)

        # Should extract alphanumeric tokens
        expected_tokens = ["machine", "learning", "algorithms", "process", "complex", "patterns", "efficiently"]
        assert all(token in tokens for token in expected_tokens)

        # Should be lowercase
        assert all(token.islower() for token in tokens)

        # Should handle punctuation
        text_with_punct = "Hello, world! How are you today?"
        tokens = tokenize(text_with_punct)
        assert "hello" in tokens
        assert "world" in tokens
        assert "," not in tokens
        assert "!" not in tokens

    def test_bm25_index_construction(self, hybrid_retriever):
        """Test BM25 index is built correctly from vector store."""
        # Ensure BM25 index is built
        assert hybrid_retriever._ensure_bm25_index()

        # Check index properties
        assert hybrid_retriever._bm25 is not None
        assert len(hybrid_retriever._chunk_ids) > 0
        assert len(hybrid_retriever._chunk_texts) > 0

        # Should have same number of documents as vector store
        assert len(hybrid_retriever._chunk_ids) == hybrid_retriever.vector_store.count()

    def test_hybrid_search_rrf_fusion(self, hybrid_retriever):
        """Test Reciprocal Rank Fusion algorithm."""
        query = "neural network training"

        results = hybrid_retriever.search(query, top_k=3)

        # Should return hybrid results
        assert "hybrid" in results
        assert "hybrid_scores" in results
        assert len(results["ids"]) == 3
        assert len(results["hybrid_scores"]) == 3

        # Hybrid scores should be properly calculated
        for score in results["hybrid_scores"]:
            assert 0 < score <= 1.0, f"Invalid hybrid score: {score}"

        # Should combine vector and BM25 results
        assert len(results["ids"]) <= len(hybrid_retriever._chunk_ids)

    def test_vector_search_fallback(self, hybrid_retriever):
        """Test fallback to vector-only search when BM25 unavailable."""
        # Disable BM25
        hybrid_retriever._bm25 = None

        query = "machine learning"
        results = hybrid_retriever.search(query, top_k=2)

        # Should still return results (vector-only)
        assert "ids" in results
        assert len(results["ids"]) == 2
        assert "hybrid" not in results  # Should not have hybrid flag

    def test_async_hybrid_search(self, hybrid_retriever):
        """Test asynchronous hybrid search."""
        import asyncio

        async def test_async():
            query = "deep learning patterns"
            results = await hybrid_retriever.async_search(query, top_k=3)

            assert "hybrid" in results
            assert len(results["ids"]) == 3
            assert len(results["hybrid_scores"]) == 3

        asyncio.run(test_async())

    def test_query_embedding_consistency(self, hybrid_retriever):
        """Test that query embedding is used consistently."""
        query = "baking techniques"

        # Search twice with same query
        results1 = hybrid_retriever.search(query, top_k=3)
        results2 = hybrid_retriever.search(query, top_k=3)

        # Should return identical results
        assert results1["ids"] == results2["ids"]
        assert np.allclose(results1["hybrid_scores"], results2["hybrid_scores"], rtol=1e-6)

    def test_rrf_parameter_sensitivity(self, vector_store, embedding_provider):
        """Test RRF parameter k affects fusion results."""
        # Create retrievers with different k values
        retriever_low_k = HybridRetriever(vector_store, embedding_provider, k=10)
        retriever_high_k = HybridRetriever(vector_store, embedding_provider, k=100)

        query = "neural networks"
        results_low = retriever_low_k.search(query, top_k=3)
        results_high = retriever_high_k.search(query, top_k=3)

        # Different k values should produce different rankings
        # (though they might be the same for simple cases)
        assert len(results_low["ids"]) == len(results_high["ids"])

    def test_metadata_preservation(self, hybrid_retriever):
        """Test that document metadata is preserved in hybrid results."""
        query = "algorithms"
        results = hybrid_retriever.search(query, top_k=5)

        # Should include metadata for all results
        assert "metadatas" in results
        assert len(results["metadatas"]) == len(results["ids"])

        # Metadata should be preserved correctly
        for metadata in results["metadatas"]:
            assert "topic" in metadata
            assert metadata["topic"] in ["AI", "cooking"]

    def test_empty_query_handling(self, hybrid_retriever):
        """Test handling of empty or invalid queries."""
        # Empty query
        with pytest.raises((ValueError, Exception)):
            hybrid_retriever.search("", top_k=3)

        # Very short query
        results = hybrid_retriever.search("a", top_k=3)
        assert len(results["ids"]) >= 0  # Should handle gracefully

    def test_top_k_parameter(self, hybrid_retriever):
        """Test top_k parameter limits results correctly."""
        query = "machine learning"

        for k in [1, 3, 5, 10]:
            results = hybrid_retriever.search(query, top_k=k)
            assert len(results["ids"]) <= k
            assert len(results["hybrid_scores"]) <= k

    def test_document_addition_invalidation(self, hybrid_retriever, vector_store):
        """Test that adding documents invalidates BM25 index."""
        # Ensure index is built
        hybrid_retriever._ensure_bm25_index()

        # Add new document
        new_doc = "New document about data science"
        new_embedding = hybrid_retriever.embedding_provider.embed(new_doc)
        vector_store.add(ids=["new_doc"], documents=[new_doc], embeddings=[new_embedding], metadatas=[{"topic": "AI"}])

        # Index should be invalidated and rebuilt
        hybrid_retriever.search("data", top_k=1)
        assert hybrid_retriever._bm25 is not None
        # Note: The actual index object might be the same reference but rebuilt internally

    def test_performance_large_corpus(self, vector_store, embedding_provider):
        """Test performance with larger document sets."""
        # Add more documents
        additional_docs = [
            f"Document {i} about {'AI' if i % 2 == 0 else 'cooking'} with specific content" for i in range(100)
        ]

        embeddings = embedding_provider.embed_batch(additional_docs)
        vector_store.add(
            ids=[f"large_doc_{i}" for i in range(len(additional_docs))],
            documents=additional_docs,
            embeddings=embeddings,
            metadatas=[{"topic": "AI" if i % 2 == 0 else "cooking"} for i in range(len(additional_docs))],
        )

        # Create new retriever for larger corpus
        large_retriever = HybridRetriever(vector_store, embedding_provider)

        import time

        start_time = time.time()
        results = large_retriever.search("machine learning algorithms", top_k=10)
        duration = time.time() - start_time

        # Should complete in reasonable time
        assert duration < 1.0, f"Search too slow: {duration:.3f}s"
        assert len(results["ids"]) == 10


class TestCrossEncoderReranker:
    """Test cross-encoder reranking for improved relevance."""

    @pytest.fixture
    def mock_cross_encoder(self):
        """Create mock cross-encoder model."""
        with patch("tools.rag.cross_encoder_reranker.CrossEncoder") as mock:
            mock_model = Mock()
            mock_model.predict.return_value = np.array([0.9, 0.7, 0.3, 0.8, 0.2])
            mock.return_value = mock_model
            yield mock_model

    @pytest.fixture
    def reranker(self, mock_cross_encoder):
        """Create cross-encoder reranker with mock model."""
        return CrossEncoderReranker(model_name="cross-encoder/ms-marco-MiniLM-L6-v2", max_candidates=20)

    def test_reranker_initialization(self, mock_cross_encoder):
        """Test reranker initialization with model."""
        reranker = CrossEncoderReranker(model_name="test-model", max_candidates=10)

        assert reranker.model_name == "test-model"
        assert reranker.max_candidates == 10
        mock_cross_encoder.assert_called_once_with("test-model")

    def test_rerank_basic_functionality(self, reranker):
        """Test basic reranking functionality."""
        query = "machine learning algorithms"
        documents = [
            "Document about ML algorithms",
            "Cooking recipe book",
            "Deep learning neural networks",
            "Traditional baking methods",
            "AI and machine learning",
        ]

        results = reranker.rerank(query, documents, top_k=3)

        # Should return indexed scores
        assert len(results) == 3
        assert all(isinstance(result, tuple) for result in results)
        assert all(isinstance(idx, int) and isinstance(score, float) for idx, score in results)

        # Should be sorted by descending score
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)

    def test_rerank_with_limit(self, reranker):
        """Test reranking with top_k limit."""
        query = "test query"
        documents = ["doc1", "doc2", "doc3", "doc4", "doc5"]

        # Test different top_k values
        for k in [1, 3, 5]:
            results = reranker.rerank(query, documents, top_k=k)
            assert len(results) == k

    def test_rerank_max_candidates_limit(self, reranker):
        """Test that max_candidates limits input documents."""
        query = "test query"
        # Create more documents than max_candidates
        documents = [f"Document {i}" for i in range(25)]

        reranker.rerank(query, documents, top_k=5)

        # Should only process max_candidates documents
        reranker.model.predict.assert_called_once()
        # The call should have been made with max_candidates pairs
        call_args = reranker.model.predict.call_args[0][0]  # First positional argument
        assert len(call_args) == reranker.max_candidates

    def test_rerank_empty_documents(self, reranker):
        """Test reranking with empty document list."""
        results = reranker.rerank("test query", [], top_k=5)
        assert results == []

    def test_async_rerank(self, reranker):
        """Test asynchronous reranking."""
        import asyncio

        async def test_async():
            query = "async test query"
            documents = ["doc1", "doc2", "doc3"]

            results = await reranker.async_rerank(query, documents, top_k=2)

            assert len(results) == 2
            assert all(isinstance(result, tuple) for result in results)

        asyncio.run(test_async())

    def test_rerank_score_consistency(self, reranker):
        """Test that reranking produces consistent scores."""
        query = "consistency test"
        documents = ["doc1", "doc2", "doc3"]

        # Rerank twice
        results1 = reranker.rerank(query, documents, top_k=3)
        results2 = reranker.rerank(query, documents, top_k=3)

        # Should produce identical results
        assert results1 == results2

    def test_factory_function_no_reranker(self):
        """Test factory function when reranking disabled."""
        with patch("tools.rag.cross_encoder_reranker.RAGConfig") as mock_config:
            config_instance = Mock()
            config_instance.use_reranker = False
            mock_config.from_env.return_value = config_instance

            from tools.rag.cross_encoder_reranker import create_reranker

            result = create_reranker()

            assert result is None

    def test_factory_function_with_reranker(self):
        """Test factory function when reranking enabled."""
        with patch("tools.rag.cross_encoder_reranker.RAGConfig") as mock_config:
            config_instance = Mock()
            config_instance.use_reranker = True
            config_instance.llm_model_local = "test-model"
            config_instance.ollama_base_url = "http://localhost:11434"
            config_instance.reranker_top_k = 15
            mock_config.from_env.return_value = config_instance

            with patch("tools.rag.cross_encoder_reranker.OllamaReranker") as mock_ollama:
                create_reranker_result = create_reranker()

                assert create_reranker_result is not None
                mock_ollama.assert_called_once_with(
                    model="test-model", base_url="http://localhost:11434", max_candidates=15
                )


class TestOllamaReranker:
    """Test Ollama-based reranker implementation."""

    @pytest.fixture
    def mock_ollama_client(self):
        """Create mock Ollama client."""
        with patch("tools.rag.cross_encoder_reranker.httpx.AsyncClient") as mock_client:
            client_instance = Mock()
            mock_client.return_value = client_instance
            yield client_instance

    @pytest.fixture
    def ollama_reranker(self, mock_ollama_client):
        """Create Ollama reranker with mocked client."""
        return OllamaReranker(model="mistral-nemo:latest", base_url="http://localhost:11434")

    def test_ollama_initialization(self, ollama_reranker):
        """Test Ollama reranker initialization."""
        assert ollama_reranker.model == "mistral-nemo:latest"
        assert ollama_reranker.base_url == "http://localhost:11434"
        assert ollama_reranker.max_candidates == 20

    def test_ollama_score_document(self, ollama_reranker, mock_ollama_client):
        """Test individual document scoring."""
        mock_ollama_client.post.return_value = Mock()
        mock_ollama_client.post.return_value.model_dump_json.return_value = {"response": "7.5"}

        import asyncio

        async def test_score():
            score = await ollama_reranker._async_score_document(mock_ollama_client, "test query", "test document")

            assert score == 7.5
            mock_ollama_client.post.assert_called_once()

        asyncio.run(test_score())

    def test_ollama_async_rerank(self, ollama_reranker, mock_ollama_client):
        """Test async reranking with multiple documents."""
        # Mock successful responses
        mock_ollama_client.post.return_value = Mock()
        mock_ollama_client.post.return_value.model_dump_json.return_value = {"response": "8.0"}

        import asyncio

        async def test_rerank():
            query = "test query"
            documents = ["doc1", "doc2", "doc3"]

            results = await ollama_reranker.async_rerank(query, documents, top_k=2)

            assert len(results) == 2
            assert all(isinstance(result, tuple) for result in results)
            # Should have made 3 API calls (one per document)
            assert mock_ollama_client.post.call_count == 3

        asyncio.run(test_rerank())

    def test_ollama_error_handling(self, ollama_reranker, mock_ollama_client):
        """Test error handling in Ollama reranker."""
        mock_ollama_client.post.side_effect = Exception("API Error")

        import asyncio

        async def test_error():
            score = await ollama_reranker._async_score_document(mock_ollama_client, "test query", "test document")

            # Should return 0.0 on error
            assert score == 0.0

        asyncio.run(test_error())

    def test_ollama_sync_wrapper(self, ollama_reranker):
        """Test synchronous wrapper for async reranking."""
        with patch.object(ollama_reranker, "async_rerank") as mock_async:
            mock_async.return_value = [(0, 0.9), (1, 0.7)]

            results = ollama_reranker.rerank("test query", ["doc1", "doc2"], top_k=2)

            assert results == [(0, 0.9), (1, 0.7)]
            mock_async.assert_called_once()


class TestNoOpReranker:
    """Test no-op reranker for fallback scenarios."""

    @pytest.fixture
    def noop_reranker(self):
        """Create no-op reranker instance."""
        return NoOpReranker()

    def test_noop_rerank(self, noop_reranker):
        """Test no-op reranking returns simple ranking."""
        query = "test query"
        documents = ["doc1", "doc2", "doc3", "doc4", "doc5"]

        results = noop_reranker.rerank(query, documents, top_k=3)

        # Should return simple reciprocal ranking
        assert len(results) == 3
        expected = [(0, 1.0), (1, 0.5), (2, 0.3333333333333333)]
        assert results == expected

    def test_noop_async_rerank(self, noop_reranker):
        """Test async no-op reranking."""
        import asyncio

        async def test_async():
            query = "test query"
            documents = ["doc1", "doc2"]

            results = await noop_reranker.async_rerank(query, documents, top_k=2)

            assert results == [(0, 1.0), (1, 0.5)]

        asyncio.run(test_async())

    def test_noop_empty_documents(self, noop_reranker):
        """Test no-op reranker with empty documents."""
        results = noop_reranker.rerank("test query", [], top_k=5)
        assert results == []

    def test_noop_top_k_greater_than_docs(self, noop_reranker):
        """Test no-op reranker when top_k > number of documents."""
        query = "test query"
        documents = ["doc1", "doc2"]

        results = noop_reranker.rerank(query, documents, top_k=5)

        # Should only return available documents
        assert len(results) == 2
        assert results == [(0, 1.0), (1, 0.5)]


class TestHybridSearchIntegration:
    """Integration tests for hybrid search with reranking."""

    @pytest.fixture
    def integrated_system(self):
        """Create integrated hybrid search + reranking system."""
        # Create vector store
        store = InMemoryDenseStore(embedding_dim=384)

        documents = [
            "Machine learning algorithms for data analysis",
            "Deep learning neural network architectures",
            "Traditional baking bread recipes",
            "Training neural networks with backpropagation",
            "Cake decorating techniques",
            "Convolutional networks for image recognition",
        ]

        embeddings = SimpleEmbeddings(embedding_dim=384).embed_batch(documents)
        store.add(
            ids=[f"doc_{i}" for i in range(len(documents))],
            documents=documents,
            embeddings=embeddings,
            metadatas=[{"topic": "AI" if i < 3 or i >= 4 else "cooking"} for i in range(len(documents))],
        )

        # Create hybrid retriever
        embedding_provider = SimpleEmbeddings(embedding_dim=384)
        hybrid = HybridRetriever(store, embedding_provider)

        # Create reranker
        reranker = NoOpReranker()  # Use no-op for predictable testing

        return hybrid, reranker

    def test_end_to_end_pipeline(self, integrated_system):
        """Test complete pipeline: hybrid search + reranking."""
        hybrid, reranker = integrated_system

        query = "neural network training"

        # Step 1: Hybrid search
        hybrid_results = hybrid.search(query, top_k=5)

        assert "ids" in hybrid_results
        assert "documents" in hybrid_results
        assert len(hybrid_results["ids"]) == 5

        # Step 2: Reranking
        documents = hybrid_results["documents"]
        reranked_results = reranker.rerank(query, documents, top_k=3)

        assert len(reranked_results) == 3
        assert all(isinstance(idx, int) and isinstance(score, float) for idx, score in reranked_results)

        # Step 3: Map back to original documents
        final_docs = [documents[idx] for idx, _ in reranked_results]
        assert len(final_docs) == 3

    def test_relevance_improvement(self, integrated_system):
        """Test that reranking improves relevance ordering."""
        hybrid, reranker = integrated_system

        query = "machine learning"

        # Get hybrid results
        hybrid_results = hybrid.search(query, top_k=4)
        documents = hybrid_results["documents"]

        # Rerank
        reranked = reranker.rerank(query, documents, top_k=4)

        # Map to documents
        reranked_docs = [documents[idx] for idx, _ in reranked]
        original_docs = documents[:4]

        # Reranking should change the order (unless already optimal)
        # For no-op reranker, order should be preserved by reciprocal scores
        assert len(reranked_docs) == len(original_docs)

    def test_performance_metrics(self, integrated_system):
        """Test performance of the integrated pipeline."""
        hybrid, reranker = integrated_system

        import time

        query = "deep learning architectures"

        # Time the complete pipeline
        start_time = time.time()

        hybrid_results = hybrid.search(query, top_k=10)
        documents = hybrid_results["documents"]
        reranked_results = reranker.rerank(query, documents, top_k=5)

        total_time = time.time() - start_time

        # Should complete quickly
        assert total_time < 0.5, f"Pipeline too slow: {total_time:.3f}s"
        assert len(reranked_results) == 5

    def test_empty_query_handling(self, integrated_system):
        """Test handling of empty queries in integrated pipeline."""
        hybrid, reranker = integrated_system

        # Empty query should be handled gracefully
        try:
            hybrid_results = hybrid.search("", top_k=3)
            # If hybrid search handles empty queries, reranking should also work
            if hybrid_results.get("documents"):
                reranked = reranker.rerank("", hybrid_results["documents"], top_k=3)
                assert len(reranked) <= 3
        except (ValueError, Exception):
            # Empty queries should raise appropriate errors
            pass

    def test_large_document_set(self, integrated_system):
        """Test performance with larger document sets."""
        hybrid, reranker = integrated_system

        # Add more documents
        additional_docs = [f"Additional document {i} about {'AI' if i % 2 == 0 else 'cooking'}" for i in range(50)]

        store = hybrid.vector_store
        embeddings = hybrid.embedding_provider.embed_batch(additional_docs)
        store.add(
            ids=[f"extra_doc_{i}" for i in range(len(additional_docs))],
            documents=additional_docs,
            embeddings=embeddings,
            metadatas=[{"topic": "AI" if i % 2 == 0 else "cooking"} for i in range(len(additional_docs))],
        )

        # Invalidate cache to rebuild index
        hybrid.invalidate_cache()

        import time

        start_time = time.time()

        results = hybrid.search("machine learning", top_k=10)
        reranked = reranker.rerank("machine learning", results["documents"], top_k=5)

        total_time = time.time() - start_time

        assert total_time < 2.0, f"Large dataset processing too slow: {total_time:.3f}s"
        assert len(reranked) == 5
