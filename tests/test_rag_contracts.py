"""
Contract tests for RAG implementations.

These tests verify that all RAG implementations conform to the defined interfaces.
Run against VectorStore, InMemoryIndex, and Retriever.
"""

from __future__ import annotations

import hashlib

import pytest

pytest.importorskip("chromadb")

from grid.rag import BaseIndex, InMemoryIndex, ScoredChunk, normalize_results, to_scored_chunk

try:
    import tools.rag.types  # noqa: F401
except ModuleNotFoundError:
    pytest.skip("RAG types module not available", allow_module_level=True)
from tools.rag.store import VectorStore

try:
    from tools.rag.retrieval.retriever import Retriever
except ModuleNotFoundError:
    try:
        from tools.rag.retriever import Retriever
    except ModuleNotFoundError:
        pytest.skip("Retriever implementation not available", allow_module_level=True)

# =============================================================================
# Contract Compliance Tests
# =============================================================================


class TestScoredChunkContract:
    """Test ScoredChunk canonical type behavior."""

    def test_scored_chunk_is_frozen(self) -> None:
        """ScoredChunk should be immutable."""
        chunk = ScoredChunk(chunk_id="c1", text="hello", score=0.9)
        from dataclasses import FrozenInstanceError
        with pytest.raises(FrozenInstanceError):
            chunk.text = "modified"  # type: ignore

    def test_scored_chunk_requires_numeric_score(self) -> None:
        """Score must be numeric."""
        with pytest.raises(TypeError):
            ScoredChunk(chunk_id="c1", text="hello", score="high")  # type: ignore

    def test_scored_chunk_equality(self) -> None:
        """Identical ScoredChunks should be equal."""
        c1 = ScoredChunk(chunk_id="c1", text="hello", score=0.9)
        c2 = ScoredChunk(chunk_id="c1", text="hello", score=0.9)
        assert c1 == c2

    def test_normalize_results_adapter(self) -> None:
        """normalize_results should convert legacy format to ScoredChunk list."""
        docs = ["doc1 text", "doc2 text"]
        scores = [0.9, 0.7]
        metas = [{"source": "a"}, {"source": "b"}]

        result = normalize_results(docs, scores, metas)

        assert len(result) == 2
        assert all(isinstance(r, ScoredChunk) for r in result)
        assert result[0].text == "doc1 text"
        assert result[0].score == 0.9
        assert result[1].text == "doc2 text"

    def test_to_scored_chunk_factory(self) -> None:
        """to_scored_chunk should create valid ScoredChunk."""
        chunk = to_scored_chunk(text="hello world", score=0.85)
        assert isinstance(chunk, ScoredChunk)
        assert chunk.text == "hello world"
        assert chunk.score == 0.85
        assert chunk.chunk_id  # Should have auto-generated ID


class TestInMemoryIndexContract:
    """Test InMemoryIndex conforms to BaseIndex contract."""

    def test_inherits_from_base_index(self) -> None:
        """InMemoryIndex should inherit from BaseIndex."""
        idx = InMemoryIndex()
        assert isinstance(idx, BaseIndex)

    def test_add_documents_interface(self) -> None:
        """add_documents should accept (ids, texts, metadatas)."""
        idx = InMemoryIndex()
        idx.add_documents(ids=["d1", "d2"], texts=["first doc", "second doc"], metadatas=[{"type": "a"}, {"type": "b"}])
        assert len(idx) == 2

    def test_search_returns_scored_chunks(self) -> None:
        """search should return List[ScoredChunk]."""
        idx = InMemoryIndex()
        idx.add_documents(ids=["d1"], texts=["apple banana cherry"], metadatas=[{}])
        results = idx.search("apple", top_k=1)

        assert isinstance(results, list)
        assert len(results) >= 1
        assert isinstance(results[0], ScoredChunk)
        assert results[0].score >= 0

    def test_search_ordering_is_stable(self) -> None:
        """Search results with equal scores should have stable ordering."""
        idx = InMemoryIndex()
        # Add docs that will have similar scores
        idx.add_documents(ids=["d1", "d2", "d3"], texts=["word", "word", "word"], metadatas=[{}, {}, {}])

        # Run multiple times - should be deterministic
        results1 = [r.chunk_id for r in idx.search("word", top_k=3)]
        results2 = [r.chunk_id for r in idx.search("word", top_k=3)]
        assert results1 == results2, "Search ordering should be deterministic"

    def test_len_returns_chunk_count(self) -> None:
        """__len__ should return number of indexed items."""
        idx = InMemoryIndex()
        assert len(idx) == 0
        idx.add_documents(ids=["d1"], texts=["hello"], metadatas=[{}])
        assert len(idx) == 1


class TestRetrieverContract:
    """Test Retriever works with both index types."""

    def test_retriever_with_inmemory_index(self) -> None:
        """Retriever should work with InMemoryIndex."""
        idx = InMemoryIndex()
        idx.add_documents(ids=["d1"], texts=["the quick brown fox"], metadatas=[{}])

        retr = Retriever(idx)
        results = retr.retrieve_with_scores("fox", top_k=1)

        assert len(results) >= 1
        chunk, score = results[0]
        assert hasattr(chunk, "text")
        assert isinstance(score, float)

    def test_retriever_with_vector_store(self) -> None:
        """Retriever should work with VectorStore."""
        store = VectorStore()
        store.add(ids=["d1"], docs=["the lazy dog"], embeddings=[{"lazy": 1.0, "dog": 1.0}], metadatas=[{}])

        retr = Retriever(store)
        results = retr.retrieve_with_scores("lazy dog", top_k=1)

        assert len(results) >= 1
        chunk, score = results[0]
        assert hasattr(chunk, "text")

    def test_retrieve_scored_returns_list(self) -> None:
        """retrieve_scored should return List[ScoredChunk]."""
        idx = InMemoryIndex()
        idx.add_documents(ids=["d1"], texts=["hello world"], metadatas=[{}])

        retr = Retriever(idx)
        results = retr.retrieve_scored("hello", top_k=1)

        assert isinstance(results, list)
        assert len(results) >= 1


# =============================================================================
# Loader Integrity Tests
# =============================================================================


class TestLoaderIntegrity:
    """Test NDJSON and persistence integrity."""

    def test_ndjson_roundtrip_preserves_count(self) -> None:
        """NDJSON save/load should preserve document count."""
        store = VectorStore()
        store.add(
            ids=["d1", "d2"],
            docs=["first doc", "second doc"],
            embeddings=[{"a": 1.0}, {"b": 1.0}],
            metadatas=[{"idx": 0}, {"idx": 1}],
        )

        ndjson = store.to_ndjson()
        loaded = VectorStore.from_ndjson(ndjson)

        assert len(loaded) == len(store)
        assert len(loaded.docs) == 2

    def test_ndjson_roundtrip_preserves_content(self) -> None:
        """NDJSON save/load should preserve document content."""
        store = VectorStore()
        store.add(ids=["d1"], docs=["unique content 12345"], embeddings=[{"x": 1.0}], metadatas=[{"source": "test"}])

        ndjson = store.to_ndjson()
        loaded = VectorStore.from_ndjson(ndjson)

        assert loaded.docs[0] == "unique content 12345"
        assert loaded.metadatas[0]["source"] == "test"

    def test_duplicate_load_detection(self) -> None:
        """Loading same data twice should result in duplicates (no auto-dedup)."""
        store = VectorStore()
        store.add(ids=["d1"], docs=["doc content"], embeddings=[{"a": 1.0}], metadatas=[{}])

        ndjson = store.to_ndjson()

        # Load into same store twice
        loaded1 = VectorStore.from_ndjson(ndjson)
        # Manually add again to simulate double-load
        for line in ndjson:
            import json

            data = json.loads(line)
            loaded1.ids.append(data["id"])
            loaded1.docs.append(data["doc"])
            loaded1.embeddings.append(data["embedding"])
            loaded1.metadatas.append(data["metadata"])

        # Should have duplicates
        assert len(loaded1) == 2

    def test_id_uniqueness_check(self) -> None:
        """Verify we can detect duplicate IDs after loading."""
        store = VectorStore()
        store.add(
            ids=["d1", "d1"],  # Duplicate ID
            docs=["first", "second"],
            embeddings=[{"a": 1.0}, {"b": 1.0}],
            metadatas=[{}, {}],
        )

        # Check for duplicates
        unique_ids = set(store.ids)
        has_duplicates = len(unique_ids) < len(store.ids)
        assert has_duplicates, "Should detect duplicate IDs"

    def test_content_hash_uniqueness(self) -> None:
        """Verify we can detect duplicate content via hashing."""
        store = VectorStore()
        store.add(
            ids=["d1", "d2"],
            docs=["same content", "same content"],  # Duplicate content
            embeddings=[{"a": 1.0}, {"b": 1.0}],
            metadatas=[{}, {}],
        )

        # Check for content duplicates via hash
        content_hashes = [hashlib.md5(doc.encode()).hexdigest() for doc in store.docs]
        unique_hashes = set(content_hashes)
        has_content_duplicates = len(unique_hashes) < len(content_hashes)
        assert has_content_duplicates, "Should detect duplicate content"


# =============================================================================
# Sorting Determinism Tests
# =============================================================================


class TestSortingDeterminism:
    """Test that all sorting operations are deterministic."""

    def test_search_with_tied_scores(self) -> None:
        """Search should be deterministic when scores are tied."""
        idx = InMemoryIndex()
        # Create docs that will have identical Jaccard scores
        idx.add_documents(ids=["a", "b", "c"], texts=["test word", "test word", "test word"], metadatas=[{}, {}, {}])

        # Run 10 times and verify order is always the same
        first_result = None
        for _ in range(10):
            result = [r.chunk_id for r in idx.search("test", top_k=3)]
            if first_result is None:
                first_result = result
            else:
                assert result == first_result, "Results should be deterministic"

    def test_vector_store_query_determinism(self) -> None:
        """VectorStore query should be deterministic."""
        store = VectorStore()
        store.add(
            ids=["a", "b", "c"],
            docs=["cat dog", "cat dog", "cat dog"],
            embeddings=[{"cat": 1.0, "dog": 1.0}] * 3,
            metadatas=[{}, {}, {}],
        )

        query_emb = {"cat": 1.0, "dog": 1.0}
        first_result = None
        for _ in range(10):
            docs, _, _ = store.query(query_emb, k=3)
            if first_result is None:
                first_result = docs
            else:
                assert docs == first_result, "Query results should be deterministic"
