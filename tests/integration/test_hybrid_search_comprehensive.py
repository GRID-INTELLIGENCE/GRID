"""
Comprehensive hybrid search and reranker tests.
Tests combination of vector and keyword search with reranking capabilities.

Uses conditional imports so mock-based tests always run.
Real dependency tests (HybridRetriever, CrossEncoderReranker) run only when available.
"""

import time
from unittest.mock import Mock, patch

import numpy as np
import pytest

# Conditional imports - mock-based tests always run
HAS_HYBRID_RETRIEVER = False
HAS_CROSS_ENCODER = False
HAS_RAG_TYPES = False

try:
    from tools.rag.hybrid_retriever import HybridRetriever

    HAS_HYBRID_RETRIEVER = True
except (ImportError, OSError):
    HybridRetriever = None

try:
    from tools.rag.cross_encoder_reranker import CrossEncoderReranker

    HAS_CROSS_ENCODER = True
except (ImportError, OSError):
    CrossEncoderReranker = None

try:
    from tools.rag.types import Document, ScoredChunk
    from tools.rag.vector_store.in_memory_dense import InMemoryDenseStore

    HAS_RAG_TYPES = True
except (ImportError, OSError):
    Document = None
    ScoredChunk = None
    InMemoryDenseStore = None

requires_hybrid = pytest.mark.skipif(
    not HAS_HYBRID_RETRIEVER, reason="HybridRetriever not available (HuggingFace Hub conflict)"
)
requires_cross_encoder = pytest.mark.skipif(
    not HAS_CROSS_ENCODER,
    reason="Cross-encoder requires sentence-transformers and torch (needs VC++ Redistributable)",
)
requires_rag_types = pytest.mark.skipif(not HAS_RAG_TYPES, reason="RAG types (Document, ScoredChunk) not available")


@requires_hybrid
@requires_rag_types
class TestHybridSearch:
    """Test hybrid search combining vector and keyword search"""

    @pytest.fixture
    def sample_documents(self):
        """Create diverse document corpus for testing"""
        return [
            Document(
                content="The Q1 financial report shows revenue of $5.2 million from software sales",
                metadata={"type": "financial", "quarter": "Q1", "year": 2024},
                id="doc_1",
            ),
            Document(
                content="Quarter 1 marketing expenses were $800K for digital campaigns",
                metadata={"type": "financial", "quarter": "Q1", "year": 2024},
                id="doc_2",
            ),
            Document(
                content="AI models require significant computational resources for training",
                metadata={"type": "technical", "topic": "AI", "complexity": "high"},
                id="doc_3",
            ),
            Document(
                content="Python is the preferred programming language for machine learning",
                metadata={"type": "technical", "topic": "programming", "language": "python"},
                id="doc_4",
            ),
            Document(
                content="The company invested $3.5M in AI infrastructure during Q1",
                metadata={"type": "financial", "quarter": "Q1", "category": "investment"},
                id="doc_5",
            ),
            Document(
                content="Machine learning algorithms improve with large datasets",
                metadata={"type": "technical", "topic": "AI", "method": "algorithmic"},
                id="doc_6",
            ),
            Document(
                content="Q2 financial projections show 15% growth in AI software revenue",
                metadata={"type": "financial", "quarter": "Q2", "category": "projection"},
                id="doc_7",
            ),
            Document(
                content="Deep learning architectures use neural networks for pattern recognition",
                metadata={"type": "technical", "topic": "AI", "method": "neural"},
                id="doc_8",
            ),
        ]

    @pytest.fixture
    def hybrid_retriever(self):
        """Setup hybrid retriever with mock components"""
        vector_store = InMemoryDenseStore(embedding_dim=384)
        bm25_retriever = Mock()

        retriever = HybridRetriever(
            vector_store=vector_store,
            bm25_retriever=bm25_retriever,
            alpha=0.5,  # Equal weight for vector and keyword
        )

        return retriever

    def test_hybrid_vs_vector_only_keyword_query(self, hybrid_retriever, sample_documents):
        """Scenario: Hybrid should outperform pure vector search for keyword-heavy queries"""
        # Setup BM25 to return keyword matches
        financial_docs = [doc for doc in sample_documents if doc.metadata["type"] == "financial"]
        hybrid_retriever.bm25_retriever.search.return_value = financial_docs[:3]

        # Add documents to vector store
        hybrid_retriever.vector_store.add_documents(sample_documents)

        # Query: Keyword-heavy financial query
        query = "Q1 financial revenue million"

        # Mock BM25 results (keyword relevance)

        # Get vector-only results
        vector_results = hybrid_retriever.vector_only_search(query, k=4)

        # Get hybrid results
        hybrid_results = hybrid_retriever.hybrid_search(query, k=4)

        # Assertions
        assert len(hybrid_results) == 4, "Hybrid should return k=4 results"
        assert len(vector_results) == 4, "Vector search should return k=4 results"

        # Financial documents should be prioritized in hybrid search
        hybrid_types = [r.metadata.get("type") for r in hybrid_results[:2]]
        vector_types = [r.metadata.get("type") for r in vector_results[:2]]

        # Hybrid should have more financial docs in top results
        hybrid_financial_count = sum(1 for t in hybrid_types if t == "financial")
        vector_financial_count = sum(1 for t in vector_types if t == "financial")

        assert hybrid_financial_count >= vector_financial_count, (
            "Hybrid search should prioritize keyword matches for financial query"
        )

    def test_hybrid_vs_keyword_only_semantic_query(self, hybrid_retriever, sample_documents):
        """Scenario: Hybrid should outperform pure keyword search for semantic queries"""
        # Setup BM25 with limited keyword matches
        limited_results = [doc for doc in sample_documents if "programming" in doc.content.lower()]
        hybrid_retriever.bm25_retriever.search.return_value = limited_results

        hybrid_retriever.vector_store.add_documents(sample_documents)

        # Query: Semantic query about machine learning concepts
        query = "neural networks and pattern recognition algorithms"

        # Get results
        hybrid_results = hybrid_retriever.hybrid_search(query, k=3)

        # Should prioritize AI/ML documents even with limited keyword matches
        [r.metadata.get("topic") for r in hybrid_results]
        ml_content_count = sum(
            1
            for r in hybrid_results
            if any(keyword in r.content.lower() for keyword in ["learning", "neural", "algorithms"])
        )

        assert ml_content_count >= 2, "Hybrid should find semantic matches for ML query"

    def test_alpha_parameter_weighting(self, sample_documents):
        """Scenario: Test different alpha values for hybrid weighting"""
        vector_store = InMemoryDenseStore(embedding_dim=384)
        bm25_retriever = Mock()

        vector_store.add_documents(sample_documents)

        # Test different alpha values
        alpha_values = [0.0, 0.25, 0.5, 0.75, 1.0]
        results_by_alpha = {}

        for alpha in alpha_values:
            retriever = HybridRetriever(vector_store=vector_store, bm25_retriever=bm25_retriever, alpha=alpha)

            # Mock consistent BM25 results
            bm25_retriever.search.return_value = sample_documents[:3]

            query = "machine learning AI"
            results = retriever.hybrid_search(query, k=3)
            results_by_alpha[alpha] = [r.id for r in results]

        # Edge cases
        vector_only = results_by_alpha[1.0]  # Pure vector
        keyword_only = results_by_alpha[0.0]  # Pure keyword

        assert vector_only != keyword_only, "Pure vector and pure keyword should produce different results"

        # Hybrid should be different from both extremes
        hybrid = results_by_alpha[0.5]
        assert hybrid != vector_only and hybrid != keyword_only, "Hybrid results should differ from pure methods"

    def test_missing_component_handling(self, sample_documents):
        """Scenario: Handle missing vector store or BM25 gracefully"""
        # Test without BM25
        vector_store = InMemoryDenseStore(embedding_dim=384)
        vector_store.add_documents(sample_documents)

        retriever_no_bm25 = HybridRetriever(
            vector_store=vector_store,
            bm25_retriever=None,
            alpha=1.0,  # Force vector-only
        )

        results = retriever_no_bm25.hybrid_search("machine learning", k=2)
        assert len(results) == 2, "Should work with only vector store"

        # Test without vector store
        bm25_retriever = Mock()
        bm25_retriever.search.return_value = sample_documents[:2]

        retriever_no_vector = HybridRetriever(
            vector_store=None,
            bm25_retriever=bm25_retriever,
            alpha=0.0,  # Force keyword-only
        )

        results = retriever_no_vector.hybrid_search("financial report", k=2)
        assert len(results) == 2, "Should work with only BM25"

    def test_performance_benchmarks(self, hybrid_retriever, sample_documents):
        """Scenario: Performance testing for hybrid search"""
        hybrid_retriever.vector_store.add_documents(sample_documents)
        hybrid_retriever.bm25_retriever.search.return_value = sample_documents[:5]

        # Benchmark search times
        queries = [
            "financial revenue Q1",
            "machine learning algorithms",
            "AI infrastructure investment",
            "neural networks pattern recognition",
            "marketing expenses digital campaigns",
        ]

        search_times = []
        for query in queries:
            start_time = time.time()
            results = hybrid_retriever.hybrid_search(query, k=5)
            duration = time.time() - start_time
            search_times.append(duration)

            assert len(results) == 5, f"Should return 5 results for query: {query}"

        avg_time = np.mean(search_times)
        max_time = max(search_times)

        # Performance assertions
        assert avg_time < 0.5, f"Average search time {avg_time:.3f}s too slow"
        assert max_time < 1.0, f"Max search time {max_time:.3f}s too slow"


@requires_cross_encoder
@requires_rag_types
class TestCrossEncoderReranker:
    """Test cross-encoder reranking for result quality improvement"""

    @pytest.fixture
    def sample_documents_for_reranking(self):
        """Documents with varying relevance for reranking tests"""
        return [
            Document(
                content="Python programming tutorial for machine learning beginners",
                metadata={"topic": "programming", "difficulty": "beginner"},
                id="rerank_1",
            ),
            Document(
                content="Advanced machine learning with Python and TensorFlow",
                metadata={"topic": "ML", "difficulty": "advanced"},
                id="rerank_2",
            ),
            Document(
                content="Python best practices in software development",
                metadata={"topic": "programming", "difficulty": "intermediate"},
                id="rerank_3",
            ),
            Document(
                content="Cooking with Python: Not about programming",
                metadata={"topic": "cooking", "difficulty": "beginner"},
                id="rerank_4",
            ),
            Document(
                content="Python snake species and their natural habitat",
                metadata={"topic": "biology", "difficulty": "expert"},
                id="rerank_5",
            ),
            Document(
                content="Python libraries for data science and analytics",
                metadata={"topic": "data science", "difficulty": "intermediate"},
                id="rerank_6",
            ),
            Document(
                content="Deep learning frameworks comparison: PyTorch vs TensorFlow",
                metadata={"topic": "ML", "difficulty": "advanced"},
                id="rerank_7",
            ),
            Document(
                content="Python web development with Django and Flask",
                metadata={"topic": "web dev", "difficulty": "intermediate"},
                id="rerank_8",
            ),
        ]

    @pytest.fixture
    def mock_reranker(self):
        """Mock cross-encoder reranker for testing"""
        with patch("tools.rag.cross_encoder_reranker.CrossEncoder") as mock_cross_encoder:
            # Mock model that returns relevance scores
            mock_model = Mock()
            mock_model.predict.return_value = np.array([0.9, 0.8, 0.3, 0.1, 0.2, 0.85, 0.7, 0.4])
            mock_cross_encoder.from_pretrained.return_value = mock_model

            reranker = CrossEncoderReranker(model="mock-model")
            return reranker, mock_model

    def test_reranker_improves_relevance_ordering(self, mock_reranker, sample_documents_for_reranking):
        """Scenario: Reranker should improve result relevance"""
        reranker, mock_model = mock_reranker

        query = "Python programming"

        # Initial results (unordered by relevance)
        initial_results = [
            ScoredChunk(
                content=doc.content,
                metadata=doc.metadata,
                id=doc.id,
                score=0.5 + (i * 0.05),  # Arbitrary initial scores
            )
            for i, doc in enumerate(sample_documents_for_reranking)
        ]

        # Apply reranking
        reranked_results = reranker.rerank(query, initial_results)

        # Verify mock was called with correct inputs
        mock_model.predict.assert_called_once()
        call_args = mock_model.predict.call_args[0][0]

        # Should call with query-document pairs
        assert len(call_args) == len(initial_results), "Should score all document-query pairs"

        # Programming-related docs should rank higher
        [r.metadata.get("topic") for r in reranked_results[:3]]
        programming_content_count = sum(
            1
            for r in reranked_results[:3]
            if any(keyword in r.content.lower() for keyword in ["programming", "python", "software"])
        )

        assert programming_content_count >= 2, "Programming docs should rank higher after reranking"

    def test_reranker_score_normalization(self, mock_reranker, sample_documents_for_reranking):
        """Scenario: Reranker scores should be properly normalized"""
        reranker, mock_model = mock_reranker

        # Mock scores that need normalization
        mock_model.predict.return_value = np.array([2.1, 1.8, 0.5, -0.3, 0.1, 1.9, 1.2, 0.7])

        query = "machine learning"
        initial_results = [
            ScoredChunk(content=doc.content, metadata=doc.metadata, id=doc.id, score=0.5)
            for doc in sample_documents_for_reranking
        ]

        reranked = reranker.rerank(query, initial_results)

        # All scores should be between 0 and 1
        for result in reranked:
            assert 0 <= result.score <= 1, f"Score {result.score} should be normalized to [0,1]"

        # Should be sorted by score (descending)
        scores = [r.score for r in reranked]
        assert scores == sorted(scores, reverse=True), "Results should be sorted by score"

        # Highest score should be close to 1.0
        assert scores[0] > 0.9, f"Highest score {scores[0]} should be near 1.0"

    def test_reranker_batch_processing(self, mock_reranker, sample_documents_for_reranking):
        """Scenario: Test batch processing efficiency"""
        reranker, mock_model = mock_reranker

        # Mock to track batch sizes
        batch_sizes = []

        def track_batches(pairs):
            batch_sizes.append(len(pairs))
            return np.random.rand(len(pairs))  # Mock scores

        mock_model.predict.side_effect = track_batches

        queries = ["Python programming", "machine learning", "data science", "web development"]

        # Test batch reranking
        for query in queries:
            initial_results = [
                ScoredChunk(content=doc.content, metadata=doc.metadata, id=doc.id, score=0.5)
                for doc in sample_documents_for_reranking
            ]

            reranked = reranker.rerank(query, initial_results, batch_size=4)

            # Should be processed in batches
            assert len(reranked) == len(initial_results), "Should return same number of results"

        # Verify batching occurred
        assert any(size < len(sample_documents_for_reranking) for size in batch_sizes), (
            "Should use batch processing for large result sets"
        )

    def test_reranker_error_handling(self, mock_reranker):
        """Scenario: Handle errors gracefully"""
        reranker, mock_model = mock_reranker

        # Mock model failure
        mock_model.predict.side_effect = Exception("Model prediction failed")

        query = "test query"
        initial_results = [ScoredChunk(content="Test document", metadata={}, id="test_1", score=0.5)]

        # Should fall back to original order or handle gracefully
        try:
            reranked = reranker.rerank(query, initial_results)
            # If successful, should maintain order
            assert len(reranked) == len(initial_results)
        except Exception:
            # Should fail gracefully with meaningful error
            pytest.fail("Reranker should handle model failures gracefully")

    def test_reranker_empty_inputs(self, mock_reranker):
        """Scenario: Handle edge cases with empty inputs"""
        reranker, _ = mock_reranker
        query = "test query"

        # Empty results
        empty_results = reranker.rerank(query, [])
        assert len(empty_results) == 0, "Empty input should return empty output"

        # Single result
        single_result = [ScoredChunk(content="Single document", metadata={}, id="single_1", score=0.5)]

        reranked_single = reranker.rerank(query, single_result)
        assert len(reranked_single) == 1, "Single result should remain single"


@requires_hybrid
@requires_cross_encoder
@requires_rag_types
class TestHybridRerankerIntegration:
    """Integration tests for hybrid search with reranking"""

    @pytest.fixture
    def sample_documents(self):
        """Create diverse document corpus for testing."""
        return [
            Document(
                content="The Q1 financial report shows revenue of $5.2 million from software sales",
                metadata={"type": "financial", "quarter": "Q1", "year": 2024},
                id="doc_1",
            ),
            Document(
                content="Quarter 1 marketing expenses were $800K for digital campaigns",
                metadata={"type": "financial", "quarter": "Q1", "year": 2024},
                id="doc_2",
            ),
            Document(
                content="AI models require significant computational resources for training",
                metadata={"type": "technical", "topic": "AI", "complexity": "high"},
                id="doc_3",
            ),
            Document(
                content="Python is the preferred programming language for machine learning",
                metadata={"type": "technical", "topic": "programming", "language": "python"},
                id="doc_4",
            ),
            Document(
                content="The company invested $3.5M in AI infrastructure during Q1",
                metadata={"type": "financial", "quarter": "Q1", "category": "investment"},
                id="doc_5",
            ),
            Document(
                content="Machine learning algorithms improve with large datasets",
                metadata={"type": "technical", "topic": "AI", "method": "algorithmic"},
                id="doc_6",
            ),
            Document(
                content="Q2 financial projections show 15% growth in AI software revenue",
                metadata={"type": "financial", "quarter": "Q2", "category": "projection"},
                id="doc_7",
            ),
            Document(
                content="Deep learning architectures use neural networks for pattern recognition",
                metadata={"type": "technical", "topic": "AI", "method": "neural"},
                id="doc_8",
            ),
        ]

    def test_hybrid_search_with_reranking_pipeline(self, sample_documents):
        """Scenario: Complete pipeline: hybrid search + reranking"""
        # Setup components
        vector_store = InMemoryDenseStore(embedding_dim=384)
        vector_store.add_documents(sample_documents)

        bm25_retriever = Mock()
        bm25_results = sample_documents[:5]  # Top 5 BM25 results
        bm25_retriever.search.return_value = bm25_results

        # Mock reranker
        with patch("tools.rag.cross_encoder_reranker.CrossEncoder") as mock_ce:
            mock_model = Mock()
            # Return relevance scores (higher for ML/AI docs)
            mock_model.predict.return_value = np.array([0.7, 0.9, 0.3, 0.8, 0.2])
            mock_ce.from_pretrained.return_value = mock_model

            reranker = CrossEncoderReranker(model="mock-model")

            # Create enhanced retriever with reranking
            hybrid_retriever = HybridRetriever(
                vector_store=vector_store, bm25_retriever=bm25_retriever, alpha=0.6, reranker=reranker
            )

            # Execute search
            query = "machine learning AI programming"
            results = hybrid_retriever.hybrid_search(query, k=4)

            # Verify results
            assert len(results) == 4, "Should return k=4 results"

            # Should be reranked (mock scores applied)
            scores = [r.score for r in results]
            assert scores == sorted(scores, reverse=True), "Results should be reranked"

            # AI/ML docs should rank higher
            ml_keywords = ["learning", "AI", "machine", "programming"]
            top_content = results[0].content.lower()
            assert any(keyword in top_content for keyword in ml_keywords), (
                "Top result should be ML-related after reranking"
            )

    def test_performance_with_reranking(self, sample_documents):
        """Scenario: Performance impact of adding reranking"""
        vector_store = InMemoryDenseStore(embedding_dim=384)
        vector_store.add_documents(sample_documents)

        bm25_retriever = Mock()
        bm25_retriever.search.return_value = sample_documents[:10]

        # Mock fast reranker
        with patch("tools.rag.cross_encoder_reranker.CrossEncoder") as mock_ce:
            mock_model = Mock()
            mock_model.predict.return_value = np.random.rand(10)
            mock_ce.from_pretrained.return_value = mock_model

            reranker = CrossEncoderReranker(model="mock-model")

            # Test without reranker
            retriever_no_rerank = HybridRetriever(vector_store=vector_store, bm25_retriever=bm25_retriever, alpha=0.5)

            start_time = time.time()
            results_no_rerank = retriever_no_rerank.hybrid_search("test query", k=5)
            time_no_rerank = time.time() - start_time

            # Test with reranker
            retriever_with_rerank = HybridRetriever(
                vector_store=vector_store, bm25_retriever=bm25_retriever, alpha=0.5, reranker=reranker
            )

            start_time = time.time()
            results_with_rerank = retriever_with_rerank.hybrid_search("test query", k=5)
            time_with_rerank = time.time() - start_time

            # Both should return 5 results
            assert len(results_no_rerank) == 5 and len(results_with_rerank) == 5

            # Reranking should add some overhead but not be excessive
            overhead_ratio = time_with_rerank / time_no_rerank
            assert overhead_ratio < 3.0, f"Reranking overhead {overhead_ratio:.1f}x should be reasonable (<3x)"
