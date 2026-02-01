"""Tests for VectorStoreRegistry factory pattern and backend management.

Phase 3 Sprint 2: RAG integration tests (5 tests for registry)
"""

from __future__ import annotations

import pytest

from tools.rag.vector_store.base import BaseVectorStore
from tools.rag.vector_store.registry import VectorStoreRegistry

# ============================================================================
# Test Group 1: Registry Registration (2 tests)
# ============================================================================


class MockVectorStore(BaseVectorStore):
    """Mock vector store for testing."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._documents = {}

    def add(
        self, ids: list[str], documents: list[str], embeddings: list[list[float]], metadatas: list[dict] | None = None
    ) -> None:
        """Add documents to mock store."""
        for i, doc_id in enumerate(ids):
            self._documents[doc_id] = {
                "document": documents[i],
                "embedding": embeddings[i],
                "metadata": metadatas[i] if metadatas else {},
            }

    def query(
        self, query_embedding: list[float], n_results: int = 5, where: dict | None = None, include: list | None = None
    ) -> dict:
        """Query mock store."""
        return {"ids": [], "documents": [], "metadatas": [], "distances": []}

    def delete(self, ids: list[str] | None = None, where: dict | None = None) -> None:
        """Delete documents from mock store."""
        if ids:
            for doc_id in ids:
                self._documents.pop(doc_id, None)

    def count(self) -> int:
        """Return document count."""
        return len(self._documents)


def test_registry_registration_success():
    """Test successful backend registration."""
    # Clear registry state
    VectorStoreRegistry._backends.clear()

    # Register mock backend
    VectorStoreRegistry.register("mock", MockVectorStore)
    assert VectorStoreRegistry.get_backend_class("mock") is MockVectorStore

    # Verify it's in the list
    backends = VectorStoreRegistry.list_backends()
    assert "mock" in backends


def test_registry_registration_duplicate_error():
    """Test that registering same backend twice raises error."""
    VectorStoreRegistry._backends.clear()

    # Register once
    VectorStoreRegistry.register("mock", MockVectorStore)

    # Try to register again
    with pytest.raises(ValueError, match="already registered"):
        VectorStoreRegistry.register("mock", MockVectorStore)


# ============================================================================
# Test Group 2: Backend Selection and Creation (2 tests)
# ============================================================================


def test_registry_create_backend():
    """Test backend instantiation through registry."""
    VectorStoreRegistry._backends.clear()
    VectorStoreRegistry.register("mock", MockVectorStore)

    # Create instance
    store = VectorStoreRegistry.create("mock", test_param="value")
    assert isinstance(store, MockVectorStore)
    assert store.kwargs["test_param"] == "value"


def test_registry_create_unknown_backend_error():
    """Test that creating unknown backend raises helpful error."""
    VectorStoreRegistry._backends.clear()
    VectorStoreRegistry.register("mock", MockVectorStore)

    # Try to create unknown backend
    with pytest.raises(ValueError, match="Unknown vector store provider"):
        VectorStoreRegistry.create("nonexistent")


# ============================================================================
# Test Group 3: Backend Unregistration and Cleanup (1 test)
# ============================================================================


def test_registry_unregister_backend():
    """Test backend unregistration."""
    VectorStoreRegistry._backends.clear()
    VectorStoreRegistry.register("mock", MockVectorStore)

    # Verify registered
    assert VectorStoreRegistry.get_backend_class("mock") is not None

    # Unregister
    VectorStoreRegistry.unregister("mock")
    assert VectorStoreRegistry.get_backend_class("mock") is None

    # Trying to create should fail
    with pytest.raises(ValueError):
        VectorStoreRegistry.create("mock")
