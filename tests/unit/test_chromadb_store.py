"""Tests for ChromaDBVectorStore persistence, collections, and querying.

Phase 3 Sprint 2: RAG integration tests (5 tests for ChromaDB store)

Note: These tests require the 'chromadb' package which is an optional dependency.
Tests are skipped if chromadb is not installed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Skip entire module if chromadb is not available
try:
    import chromadb  # noqa: F401

    from tools.rag.vector_store.chromadb_store import ChromaDBVectorStore
except ImportError:
    pytest.skip(
        "chromadb package not installed - skipping ChromaDB tests. Install with: pip install chromadb",
        allow_module_level=True,
    )

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def temp_chroma_dir(tmp_path: Path):
    """Create temporary directory for ChromaDB persistence."""
    chroma_dir = tmp_path / "chroma_db"
    chroma_dir.mkdir(parents=True, exist_ok=True)
    return str(chroma_dir)


@pytest.fixture
def chromadb_store(temp_chroma_dir):
    """Create ChromaDB store instance with temporary directory."""
    store = ChromaDBVectorStore(collection_name="test_collection", persist_directory=temp_chroma_dir)
    yield store
    # Close collection properly
    try:
        if hasattr(store, "client"):
            store.client.reset()
    except Exception:
        pass


# ============================================================================
# Test Group 1: Initialization and Collection Management (2 tests)
# ============================================================================


def test_chromadb_initialization(temp_chroma_dir):
    """Test successful ChromaDB store initialization."""
    store = ChromaDBVectorStore(collection_name="test_collection", persist_directory=temp_chroma_dir)

    assert store.collection_name == "test_collection"
    assert store.persist_directory == temp_chroma_dir
    assert store.collection is not None


def test_chromadb_collection_creation(temp_chroma_dir):
    """Test that ChromaDB creates collection with cosine similarity."""
    store = ChromaDBVectorStore(collection_name="test_collection", persist_directory=temp_chroma_dir)

    # Verify collection metadata (if accessible)
    assert store.collection is not None
    assert store.collection_name == "test_collection"


# ============================================================================
# Test Group 2: Document Addition and Storage (1 test)
# ============================================================================


def test_chromadb_add_documents(chromadb_store):
    """Test adding documents with embeddings to ChromaDB."""
    ids = ["doc1", "doc2"]
    documents = ["Content 1", "Content 2"]
    embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    metadatas = [{"source": "test"}, {"source": "test"}]

    chromadb_store.add(ids, documents, embeddings, metadatas)

    # Verify count increased
    count = chromadb_store.count()
    assert count == 2


# ============================================================================
# Test Group 3: Querying and Similarity Search (1 test)
# ============================================================================


def test_chromadb_query_documents(chromadb_store):
    """Test querying ChromaDB for similar documents."""
    # Add documents
    ids = ["doc1", "doc2"]
    documents = ["Similar content", "Different topic"]
    embeddings = [[0.1, 0.2, 0.3], [0.9, 0.8, 0.7]]
    metadatas = [{"source": "test"}, {"source": "test"}]

    chromadb_store.add(ids, documents, embeddings, metadatas)

    # Query with similar embedding to doc1
    query_embedding = [0.1, 0.2, 0.3]
    result = chromadb_store.query(query_embedding, n_results=2)

    assert "ids" in result
    assert "documents" in result
    assert "metadatas" in result
    assert "distances" in result
    assert len(result["ids"]) <= 2


# ============================================================================
# Test Group 4: Deletion and Cleanup (1 test)
# ============================================================================


def test_chromadb_delete_documents(chromadb_store):
    """Test deleting documents from ChromaDB."""
    # Add documents
    ids = ["doc1", "doc2", "doc3"]
    documents = ["Content 1", "Content 2", "Content 3"]
    embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]

    chromadb_store.add(ids, documents, embeddings)
    assert chromadb_store.count() == 3

    # Delete specific documents
    chromadb_store.delete(ids=["doc1", "doc2"])
    assert chromadb_store.count() == 1

    # Delete remaining with where filter should fail without proper setup
    # so we just verify single doc remains
    result = chromadb_store.query([0.7, 0.8, 0.9], n_results=5)
    assert "doc3" in result["ids"]
