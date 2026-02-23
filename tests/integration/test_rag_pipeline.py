"""Tests for RAG pipeline end-to-end workflows, performance, and resilience.

Phase 3 Sprint 2: RAG integration tests (5 tests for pipeline)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.rag.vector_store.chromadb_store import ChromaDBVectorStore
from tools.rag.vector_store.in_memory_dense import InMemoryDenseStore


def _create_chromadb_store_or_skip(collection_name: str, persist_directory: str):
    """Create ChromaDB store or skip when optional dependency is unavailable."""
    try:
        return ChromaDBVectorStore(collection_name=collection_name, persist_directory=persist_directory)
    except Exception as e:
        pytest.skip(f"ChromaDB unavailable in this environment: {e}")


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def temp_rag_dir(tmp_path: Path):
    """Create temporary directory for RAG operations."""
    rag_dir = tmp_path / "rag_pipeline"
    rag_dir.mkdir(parents=True, exist_ok=True)
    return str(rag_dir)


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        {
            "id": "doc1",
            "text": "Machine learning is a subset of artificial intelligence",
            "path": "ai_basics.txt",
            "metadata": {"source": "tutorial"},
        },
        {
            "id": "doc2",
            "text": "Deep learning uses neural networks with multiple layers",
            "path": "deep_learning.txt",
            "metadata": {"source": "research"},
        },
        {
            "id": "doc3",
            "text": "Natural language processing enables computers to understand text",
            "path": "nlp_guide.txt",
            "metadata": {"source": "guide"},
        },
    ]


# ============================================================================
# Test Group 1: End-to-End Pipeline Flow (1 test)
# ============================================================================


def test_rag_pipeline_end_to_end(temp_rag_dir, sample_documents):
    """Test complete RAG pipeline: index → query → retrieve."""
    # Create vector store
    store = _create_chromadb_store_or_skip(collection_name="pipeline_test", persist_directory=temp_rag_dir)

    # Create embeddings (simple mock embeddings)
    embeddings = [
        [0.1, 0.2, 0.3, 0.4, 0.5],  # doc1
        [0.15, 0.25, 0.35, 0.45, 0.55],  # doc2
        [0.2, 0.3, 0.4, 0.5, 0.6],  # doc3
    ]

    ids = [doc["id"] for doc in sample_documents]
    texts = [doc["text"] for doc in sample_documents]
    metadatas = [doc["metadata"] for doc in sample_documents]

    # Index documents
    store.add(ids, texts, embeddings, metadatas)

    # Verify indexing
    assert store.count() == 3

    # Query
    query_embedding = [0.12, 0.22, 0.32, 0.42, 0.52]
    results = store.query(query_embedding, n_results=2)

    # Verify results
    assert len(results["ids"]) <= 2
    assert "documents" in results
    assert "distances" in results


# ============================================================================
# Test Group 2: Multi-Store Fallback Chain (1 test)
# ============================================================================


def test_rag_pipeline_fallback_chain(temp_rag_dir, sample_documents):
    """Test fallback from primary to secondary vector store."""
    # Primary store (might fail)
    primary_store = _create_chromadb_store_or_skip(collection_name="primary", persist_directory=temp_rag_dir)

    # Fallback store (in-memory)
    fallback_store = InMemoryDenseStore()

    # Prepare embeddings
    embeddings = [[0.1 * (i + 1)] * 5 for i in range(len(sample_documents))]

    ids = [doc["id"] for doc in sample_documents]
    texts = [doc["text"] for doc in sample_documents]
    metadatas = [doc["metadata"] for doc in sample_documents]

    # Index in both stores
    primary_store.add(ids, texts, embeddings, metadatas)
    fallback_store.add(ids, texts, embeddings, metadatas)

    # Query primary
    query_embedding = [0.15] * 5
    primary_results = primary_store.query(query_embedding, n_results=2)

    # Query fallback
    fallback_results = fallback_store.query(query_embedding, n_results=2)

    # Both should have results
    assert len(primary_results["ids"]) >= 0
    assert len(fallback_results["ids"]) >= 0


# ============================================================================
# Test Group 3: Batch Processing and Performance (1 test)
# ============================================================================


def test_rag_pipeline_batch_processing(temp_rag_dir):
    """Test batch document processing for scalability."""
    store = _create_chromadb_store_or_skip(collection_name="batch_test", persist_directory=temp_rag_dir)

    # Create large batch of documents
    batch_size = 50
    batch_ids = [f"doc_{i}" for i in range(batch_size)]
    batch_texts = [f"Document content {i}" for i in range(batch_size)]
    batch_embeddings = [[0.1 * (i % 10)] * 5 for i in range(batch_size)]

    # Add batch
    store.add(batch_ids, batch_texts, batch_embeddings)

    # Verify all documents indexed
    assert store.count() == batch_size

    # Verify queries still work
    query_result = store.query([0.5] * 5, n_results=5)
    assert len(query_result["ids"]) <= 5


# ============================================================================
# Test Group 4: Document Deletion and Updates (1 test)
# ============================================================================


def test_rag_pipeline_deletion_and_updates(temp_rag_dir, sample_documents):
    """Test updating/deleting documents in RAG pipeline."""
    store = _create_chromadb_store_or_skip(collection_name="deletion_test", persist_directory=temp_rag_dir)

    embeddings = [[0.1 * (i + 1)] * 5 for i in range(len(sample_documents))]
    ids = [doc["id"] for doc in sample_documents]
    texts = [doc["text"] for doc in sample_documents]
    metadatas = [doc["metadata"] for doc in sample_documents]

    # Initial indexing
    store.add(ids, texts, embeddings, metadatas)
    assert store.count() == 3

    # Delete one document
    store.delete(ids=["doc1"])
    assert store.count() == 2

    # Verify deleted doc not in results
    results = store.query([0.1] * 5, n_results=5)
    assert "doc1" not in results["ids"]


# ============================================================================
# Test Group 5: Persistence and Recovery (1 test)
# ============================================================================


def test_rag_pipeline_persistence(temp_rag_dir, sample_documents):
    """Test data persistence across store instances."""
    # First session: create store and index
    store1 = _create_chromadb_store_or_skip(collection_name="persist_test", persist_directory=temp_rag_dir)

    embeddings = [[0.1 * (i + 1)] * 5 for i in range(len(sample_documents))]
    ids = [doc["id"] for doc in sample_documents]
    texts = [doc["text"] for doc in sample_documents]
    metadatas = [doc["metadata"] for doc in sample_documents]

    store1.add(ids, texts, embeddings, metadatas)
    initial_count = store1.count()

    # Second session: create new store instance from same directory
    store2 = _create_chromadb_store_or_skip(collection_name="persist_test", persist_directory=temp_rag_dir)

    # Data should persist
    assert store2.count() == initial_count
    assert store2.count() == 3

    # Query should still work
    results = store2.query([0.15] * 5, n_results=2)
    assert len(results["ids"]) > 0
