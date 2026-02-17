"""Retriever component for querying the vector store."""

from __future__ import annotations

from typing import Any

from .store import VectorStore
from .types import EmbeddingProvider

# Import contracts - use try/except for backward compatibility
try:
    from grid.rag import BaseRetriever, RetrievalResult, normalize_results  # noqa: F401

    HAS_CONTRACTS = True
except ImportError:
    HAS_CONTRACTS = False
    BaseRetriever = object  # type: ignore


class Retriever(BaseRetriever if HAS_CONTRACTS else object):  # type: ignore[misc]
    """Retrieves relevant documents from a vector store or InMemoryIndex.

    Conforms to BaseRetriever contract when available.
    """

    def __init__(self, store: VectorStore | Any, embedding_provider: EmbeddingProvider | None = None) -> None:
        self.store = store
        self.embedding_provider = embedding_provider
        # Detect if this is an InMemoryIndex (has .search method and ._ids)
        self._is_memory_index = hasattr(store, "search") and (hasattr(store, "_ids") or hasattr(store, "_texts"))

    def retrieve(
        self, query: str, k: int = 5, threshold: float = 0.0, embedding: dict[str, float] | None = None
    ) -> tuple[list[str], list[dict[str, Any]], list[float]]:
        """Retrieve documents relevant to the query.

        Args:
            query: Query string
            k: Number of documents to retrieve
            threshold: Minimum similarity threshold
            embedding: Pre-computed query embedding (optional)

        Returns:
            Tuple of (documents, metadatas, scores)
        """
        # Handle different store types
        is_chromadb = hasattr(self.store, "collection")  # ChromaDBVectorStore

        if embedding is None:
            if self.embedding_provider is None:
                if is_chromadb:
                    # ChromaDB needs dense vectors (list of floats)
                    from .embeddings.simple import SimpleEmbedding

                    fallback_provider = SimpleEmbedding(use_tfidf=False)
                    embedding = fallback_provider.embed(query)
                else:
                    # VectorStore uses sparse dict embeddings
                    words = query.lower().split()
                    embedding = {word: words.count(word) for word in set(words)}
            else:
                embedding = self.embedding_provider.embed(query)

        if is_chromadb:
            # ChromaDB expects dense vector (list of floats)
            if isinstance(embedding, dict):
                # Convert sparse dict to dense list if needed
                # Use digit keys as indices
                max_idx = max([int(k) for k in embedding.keys() if k.isdigit()] + [-1])
                if max_idx >= 0:
                    dense = [0.0] * (max_idx + 1)
                    for k, v in embedding.items():
                        if k.isdigit():
                            dense[int(k)] = v
                    embedding = dense

            result = self.store.query(embedding, n_results=k)
            docs = result.get("documents", [])
            metas = result.get("metadatas", [])
            # Convert distances to scores (lower distance = higher score)
            distances = result.get("distances", [])
            scores = [1.0 / (1.0 + d) for d in distances] if distances else [1.0] * len(docs)
            return docs, metas, scores
        else:
            # VectorStore or similar uses sparse dict embeddings
            if isinstance(embedding, (list, tuple)):
                # Convert dense list to sparse dict
                embedding = {str(i): float(v) for i, v in enumerate(embedding) if v != 0}

            return self.store.query(embedding, k=k, threshold=threshold)

    def retrieve_with_scores(self, query: str, top_k: int = 5) -> list[tuple[Any, float]]:
        """Retrieve documents with their similarity scores.

        Works with both VectorStore and InMemoryIndex.
        Returns List[Tuple[ScoredChunk, float]] for contract compliance.

        Args:
            query: Query string
            top_k: Number of documents to retrieve

        Returns:
            List of (ScoredChunk, score) tuples
        """
        if self._is_memory_index:
            # InMemoryIndex.search now returns List[ScoredChunk]
            results = self.store.search(query, top_k=top_k)
            if HAS_CONTRACTS:
                # Already ScoredChunk objects
                return [(r, r.score) for r in results]
            else:
                # Legacy tuple format
                return [(r, r.score) for r in results]
        else:
            # VectorStore returns (docs, metadatas, scores)
            docs, metas, scores = self.retrieve(query, k=top_k)
            if HAS_CONTRACTS:
                scored = normalize_results(docs, scores, metas)
                return [(chunk, chunk.score) for chunk in scored]
            else:
                from dataclasses import dataclass

                @dataclass
                class DocResult:
                    text: str
                    metadata: dict[str, Any]
                    score: float = 0.0

                return [
                    (DocResult(text=doc, metadata=meta, score=sc), sc)
                    for doc, meta, sc in zip(docs, metas, scores, strict=False)
                ]

    def retrieve_scored(self, query: str, top_k: int = 5) -> list[Any]:
        """Retrieve as List[ScoredChunk] (canonical contract method).

        Args:
            query: Query string
            top_k: Number of results

        Returns:
            List[ScoredChunk] ordered by relevance
        """
        if self._is_memory_index:
            return self.store.search(query, top_k=top_k)
        else:
            docs, metas, scores = self.retrieve(query, k=top_k)
            if HAS_CONTRACTS:
                return normalize_results(docs, scores, metas)
            return list(zip(docs, scores, metas, strict=False))  # fallback

    def retrieve_with_context(
        self, query: str, k: int = 3, max_context_length: int = 2000, separator: str = "\n\n---\n\n"
    ) -> str:
        """Retrieve documents and format as context string.

        Args:
            query: Query string
            k: Number of documents to retrieve
            max_context_length: Maximum total length of context
            separator: Separator between documents

        Returns:
            Formatted context string
        """
        docs, metadatas, scores = self.retrieve(query, k=k)

        if not docs:
            return "No relevant information found."

        # Format documents with metadata
        formatted_docs: list[str] = []
        current_length = 0

        for doc, meta, _score in zip(docs, metadatas, scores, strict=False):
            # Format document with its metadata
            if meta.get("type") == "chunk" and "path" in meta:
                formatted = f"[Source: {meta['path']} (chunk {meta.get('chunk_index', '?')})]\n{doc}"
            elif "path" in meta:
                formatted = f"[Source: {meta['path']}]\n{doc}"
            else:
                formatted = doc

            # Check if adding this would exceed the limit
            if current_length + len(formatted) > max_context_length and formatted_docs:
                break

            formatted_docs.append(formatted)
            current_length += len(formatted)

        return separator.join(formatted_docs)

    def search_by_metadata(
        self, filters: dict[str, Any], k: int | None = None
    ) -> tuple[list[str], list[dict[str, Any]], list[float]]:
        """Search documents by metadata filters.

        Args:
            filters: Dictionary of metadata key-value pairs to match
            k: Maximum number of results (None for all matches)

        Returns:
            Tuple of (documents, metadatas, scores)
        """
        docs: list[str] = []
        metas: list[dict[str, Any]] = []
        scores: list[float] = []

        for i, meta in enumerate(self.store.metadatas):
            # Check if all filters match
            matches = True
            for key, value in filters.items():
                if meta.get(key) != value:
                    matches = False
                    break

            if matches:
                docs.append(self.store.docs[i])
                metas.append(meta)
                scores.append(1.0)  # Perfect match for metadata search

                if k and len(docs) >= k:
                    break

        return docs, metas, scores

    def get_document_by_id(self, doc_id: str) -> tuple[str, dict[str, Any]] | None:
        """Get a specific document by its ID.

        Args:
            doc_id: Document ID to retrieve

        Returns:
            Tuple of (document, metadata) or None if not found
        """
        try:
            idx = self.store.ids.index(doc_id)
            return self.store.docs[idx], self.store.metadatas[idx]
        except ValueError:
            return None

    def list_sources(self) -> list[str]:
        """List all unique sources in the store."""
        sources = set()
        for meta in self.store.metadatas:
            if "path" in meta:
                sources.add(meta["path"])
        return sorted(sources)

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the store.

        Returns:
            Dictionary with store statistics
        """
        doc_types: dict[str, int] = {}
        total_length = 0

        for doc, meta in zip(self.store.docs, self.store.metadatas, strict=False):
            doc_type = meta.get("type", "unknown")
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            total_length += len(doc)

        return {
            "total_documents": len(self.store.docs),
            "total_characters": total_length,
            "average_document_length": total_length / len(self.store.docs) if self.store.docs else 0,
            "document_types": doc_types,
            "unique_sources": len(self.list_sources()),
        }
