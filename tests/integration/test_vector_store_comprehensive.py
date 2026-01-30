"""
Comprehensive vector store integration tests covering all supported backends.
Tests CRUD operations, performance, accuracy, and error handling.
"""

import time

import numpy as np
import pytest

from tools.rag.types import Document
from tools.rag.vector_store.chromadb_store import ChromaDBVectorStore
from tools.rag.vector_store.in_memory_dense import InMemoryDenseStore


class TestVectorStoreOperations:
    """Test CRUD operations for all vector stores with performance metrics"""

    @pytest.fixture(params=["chromadb", "in_memory"])
    def vector_store(self, request):
        """Parameterized fixture for testing all vector stores"""
        if request.param == "chromadb":
            store = ChromaDBVectorStore(collection_name="test_collection")
            return store
        else:
            return InMemoryDenseStore(embedding_dim=1536)

    @pytest.fixture
    def sample_documents(self) -> list[Document]:
        """Generate sample documents for testing"""
        return [
            Document(
                content="Machine learning algorithms power modern AI systems",
                metadata={"source": "ai_basics.txt", "page": 1, "topic": "AI"},
                id="doc_1",
            ),
            Document(
                content="Deep learning neural networks process complex patterns",
                metadata={"source": "deep_learning.txt", "page": 2, "topic": "AI"},
                id="doc_2",
            ),
            Document(
                content="Traditional baking methods use yeast and flour",
                metadata={"source": "cooking_basics.txt", "page": 1, "topic": "cooking"},
                id="doc_3",
            ),
            Document(
                content="Training deep learning models requires large datasets",
                metadata={"source": "model_training.txt", "page": 3, "topic": "AI"},
                id="doc_4",
            ),
        ]

    def test_add_documents_batch_performance(self, vector_store, sample_documents):
        """Scenario: Add 1000 documents in batch with performance requirements"""
        # Generate test documents
        documents = []
        for i in range(1000):
            doc = Document(
                content=f"This is test document {i} with content about {['AI', 'cooking', 'sports', 'science'][i % 4]}",
                metadata={"source": f"test_file_{i // 10}.txt", "page": i % 50, "batch": i // 100},
                id=f"doc_{i}",
            )
            documents.append(doc)

        # Performance test: should complete within reasonable time
        start_time = time.time()
        vector_store.add_documents(documents)
        duration = time.time() - start_time

        # Performance assertion (adjust based on hardware)
        assert duration < 10.0, f"Batch insert took {duration:.2f}s, expected <10s"
        assert len(vector_store) == 1000, f"Expected 1000 documents, got {len(vector_store)}"

    def test_similarity_search_accuracy(self, vector_store, sample_documents):
        """Scenario: Search for similar documents with relevance scoring and ordering"""
        vector_store.add_documents(sample_documents)

        # Test 1: AI-related query should return AI documents first
        results = vector_store.similarity_search(query="neural network training algorithms", k=3)

        # Verify all results have scores
        assert all(hasattr(result, "score") for result in results), "All results should have scores"
        assert all(0 <= result.score <= 1 for result in results), "Scores should be between 0 and 1"

        # AI documents should rank higher
        ai_topics = [result.metadata.get("topic") for result in results[:2]]
        assert all(topic == "AI" for topic in ai_topics), f"First 2 results should be AI topic, got {ai_topics}"

        # Test 2: Cooking query should return cooking documents
        cooking_results = vector_store.similarity_search(query="baking with yeast and flour", k=2)

        cooking_topics = [result.metadata.get("topic") for result in cooking_results]
        assert "cooking" in cooking_topics, "Should return cooking documents for cooking query"

    def test_metadata_filtering(self, vector_store, sample_documents):
        """Scenario: Filter search results using metadata"""
        vector_store.add_documents(sample_documents)

        # Filter by topic
        ai_results = vector_store.similarity_search(query="learning", k=10, where={"topic": "AI"})

        assert all(result.metadata.get("topic") == "AI" for result in ai_results), (
            "All results should have AI topic when filtered by AI topic"
        )

        # Filter by source
        source_results = vector_store.similarity_search(query="content", k=10, where={"source": "ai_basics.txt"})

        assert all(result.metadata.get("source") == "ai_basics.txt" for result in source_results), (
            "All results should come from specified source"
        )

    def test_error_handling_invalid_input(self, vector_store):
        """Scenario: Handle malformed input gracefully with proper error messages"""
        # Test empty document content
        with pytest.raises(ValueError, match="Document content cannot be empty"):
            vector_store.add_documents([Document(content="", metadata={})])

        # Test empty query
        with pytest.raises(ValueError, match="Query cannot be empty"):
            vector_store.similarity_search(query="", k=5)

        # Test invalid k value
        with pytest.raises(ValueError, match="k must be positive"):
            vector_store.similarity_search(query="test", k=0)

        # Test None metadata
        with pytest.raises(ValueError, match="Metadata cannot be None"):
            vector_store.add_documents([Document(content="test", metadata=None)])

    def test_document_update_and_deletion(self, vector_store, sample_documents):
        """Scenario: Update and delete documents"""
        vector_store.add_documents(sample_documents)

        initial_count = len(vector_store)
        assert initial_count == 4, f"Expected 4 documents initially, got {initial_count}"

        # Update a document
        updated_doc = Document(
            content="Updated content about advanced machine learning",
            metadata={"source": "updated.txt", "topic": "AI"},
            id="doc_1",
        )

        vector_store.update_document(updated_doc)

        # Verify update
        results = vector_store.similarity_search("advanced machine learning", k=1)
        assert len(results) == 1, "Should find updated document"
        assert results[0].id == "doc_1", "Updated document should be found"
        assert "advanced" in results[0].content, "Content should be updated"

        # Delete a document
        vector_store.delete_document("doc_3")

        assert len(vector_store) == initial_count - 1, "Document count should decrease after deletion"

        # Verify deletion
        remaining_results = vector_store.similarity_search("baking", k=10)
        cooking_ids = [result.id for result in remaining_results]
        assert "doc_3" not in cooking_ids, "Deleted document should not be found"

    def test_embedding_dimension_consistency(self, vector_store):
        """Scenario: Verify all embeddings have consistent dimensions"""
        documents = [Document(content=f"Test document {i}", metadata={"index": i}) for i in range(10)]

        vector_store.add_documents(documents)

        # Get all embeddings (if accessible)
        if hasattr(vector_store, "_embeddings"):
            embeddings = vector_store._embeddings
            assert len(set(len(emb) for emb in embeddings)) == 1, "All embeddings should have the same dimension"

    def test_persistence_and_recovery(self, vector_store, sample_documents):
        """Scenario: Test that data persists across store instances"""
        if isinstance(vector_store, InMemoryDenseStore):
            pytest.skip("In-memory store doesn't persist across instances")

        # Add documents
        vector_store.add_documents(sample_documents)
        original_count = len(vector_store)

        # Create new instance with same collection
        new_store = ChromaDBStore(collection_name="test_collection")
        new_store._ensure_collection()

        assert len(new_store) == original_count, "Data should persist across store instances"

        # Verify content
        results = new_store.similarity_search("machine learning", k=2)
        assert len(results) == 2, "Should find documents after recovery"


class TestVectorStorePerformance:
    """Performance benchmarks for vector stores"""

    @pytest.fixture
    def large_document_set(self):
        """Generate large document set for performance testing"""
        topics = ["AI", "cooking", "sports", "science", "technology", "art", "music", "history"]
        documents = []

        for i in range(5000):
            topic = topics[i % len(topics)]
            content = f"Document {i} about {topic}. " + " ".join([f"keyword_{j}_{topic}" for j in range(20)])

            doc = Document(
                content=content,
                metadata={"topic": topic, "batch": i // 100, "timestamp": time.time() - i * 60},
                id=f"perf_doc_{i}",
            )
            documents.append(doc)

        return documents

    def test_large_batch_insertion(self, large_document_set):
        """Test performance of large batch insertions"""
        store = InMemoryDenseStore(embedding_dim=1536)

        start_time = time.time()
        store.add_documents(large_document_set)
        insert_time = time.time() - start_time

        # Performance assertions
        docs_per_second = len(large_document_set) / insert_time
        assert docs_per_second > 100, f"Insertion too slow: {docs_per_second:.1f} docs/sec, expected >100"
        assert insert_time < 60, f"Insertion took {insert_time:.1f}s, expected <60s"

        assert len(store) == len(large_document_set), "All documents should be inserted"

    def test_search_performance_at_scale(self, large_document_set):
        """Test search performance with large dataset"""
        store = InMemoryDenseStore(embedding_dim=1536)
        store.add_documents(large_document_set)

        queries = [
            "artificial intelligence and machine learning",
            "baking bread with yeast",
            "football basketball soccer scores",
            "physics chemistry biology experiments",
        ]

        search_times = []
        results_counts = []

        for query in queries:
            start_time = time.time()
            results = store.similarity_search(query, k=10)
            search_time = time.time() - start_time

            search_times.append(search_time)
            results_counts.append(len(results))

        avg_search_time = np.mean(search_times)
        max_search_time = max(search_times)

        # Performance assertions
        assert avg_search_time < 0.1, f"Average search time {avg_search_time:.3f}s too slow, expected <0.1s"
        assert max_search_time < 0.5, f"Max search time {max_search_time:.3f}s too slow, expected <0.5s"
        assert all(count == 10 for count in results_counts), "All searches should return k=10 results"

    def test_memory_usage(self, large_document_set):
        """Test memory usage doesn't grow excessively"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        store = InMemoryDenseStore(embedding_dim=1536)
        store.add_documents(large_document_set)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory assertion (adjust based on available memory)
        memory_per_doc = memory_increase / len(large_document_set)
        assert memory_per_doc < 0.1, f"Memory usage too high: {memory_per_doc:.3f}MB per document, expected <0.1MB"
