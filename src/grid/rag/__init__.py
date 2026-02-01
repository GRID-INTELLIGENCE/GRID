"""GRID RAG - Retrieval Augmented Generation wrapper.

This module provides a compatibility layer and re-exports from tools.rag.
It also defines types (Doc, InMemoryIndex, RagQA) that tests expect.
"""

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

_EXPORTS = [
    "ChromaDBVectorStore",
    "ModelMode",
    "OllamaEmbedding",
    "OllamaLocalLLM",
    "RAGConfig",
    "RAGEngine",
    "chunk_text",
    "get_embedding_provider",
    "get_llm_provider",
    "index_repository",
    "read_file_content",
]


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    try:
        from grid.integration.tools_bridge import get_tools_bridge

        bridge = get_tools_bridge()
        if bridge.is_rag_available():
            return getattr(__import__("tools.rag", fromlist=[name]), name)
    except Exception:
        pass

    import importlib

    rag_module = importlib.import_module("tools.rag")
    return getattr(rag_module, name)


# --- Core Types ---


@dataclass(frozen=True)
class ScoredChunk:
    """Immutable scored chunk result from search."""

    chunk_id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate score is numeric."""
        if not isinstance(self.score, (int, float)):
            raise TypeError(f"score must be numeric, got {type(self.score).__name__}")


@dataclass
class Doc:
    """Document representation for RAG indexing."""

    doc_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


# --- Utility Functions ---


def to_scored_chunk(
    text: str,
    score: float,
    chunk_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ScoredChunk:
    """Factory function to create a ScoredChunk with auto-generated ID if needed."""
    if chunk_id is None:
        chunk_id = hashlib.md5(text.encode()).hexdigest()[:12]
    return ScoredChunk(
        chunk_id=chunk_id,
        text=text,
        score=score,
        metadata=metadata or {},
    )


def normalize_results(
    docs: list[str],
    scores: list[float],
    metadatas: list[dict[str, Any]] | None = None,
) -> list[ScoredChunk]:
    """Convert legacy (docs, scores, metadatas) format to List[ScoredChunk]."""
    if metadatas is None:
        metadatas = [{}] * len(docs)

    return [
        to_scored_chunk(text=doc, score=score, metadata=meta)
        for doc, score, meta in zip(docs, scores, metadatas, strict=False)
    ]


# --- Abstract Base Classes ---


class BaseRetriever(ABC):
    """Abstract base class for RAG retrievers."""

    @abstractmethod
    def retrieve(
        self, query: str, k: int = 5, threshold: float = 0.0
    ) -> tuple[list[str], list[dict[str, Any]], list[float]]:
        """Retrieve documents relevant to the query."""
        ...

    @abstractmethod
    def retrieve_scored(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        """Retrieve as List[ScoredChunk]."""
        ...


# Type alias for retrieval results
RetrievalResult = tuple[list[str], list[dict[str, Any]], list[float]]


class BaseIndex(ABC):
    """Abstract base class for RAG indices."""

    @abstractmethod
    def add_documents(
        self,
        ids: list[str],
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add documents to the index."""
        ...

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        """Search for relevant documents."""
        ...

    @abstractmethod
    def __len__(self) -> int:
        """Return number of indexed items."""
        ...


class InMemoryIndex(BaseIndex):
    """Simple in-memory index for RAG retrieval."""

    def __init__(self) -> None:
        self._ids: list[str] = []
        self._texts: list[str] = []
        self._metadatas: list[dict[str, Any]] = []

    def add_documents(
        self,
        ids: list[str] | None = None,
        texts: list[str] | None = None,
        metadatas: list[dict[str, Any]] | None = None,
        docs: list[Doc] | None = None,  # Legacy support
    ) -> None:
        """Add documents to the index."""
        # Handle legacy Doc list input
        if docs is not None:
            for doc in docs:
                self._ids.append(doc.doc_id)
                self._texts.append(doc.text)
                self._metadatas.append(doc.metadata)
            return

        # Standard interface
        if ids is None or texts is None:
            raise ValueError("ids and texts are required")

        if metadatas is None:
            metadatas = [{}] * len(ids)

        self._ids.extend(ids)
        self._texts.extend(texts)
        self._metadatas.extend(metadatas)

    def add_documents_chunked(self, docs: list[Doc], chunk_size: int = 100, overlap: int = 10) -> None:
        """Add documents with chunking (legacy interface)."""
        for doc in docs:
            words = doc.text.split()
            for i in range(0, max(1, len(words)), max(1, chunk_size - overlap)):
                chunk_words = words[i : i + chunk_size]
                chunk_text = " ".join(chunk_words)
                self._ids.append(f"{doc.doc_id}_chunk_{i}")
                self._texts.append(chunk_text)
                self._metadatas.append(doc.metadata)

    def search(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        """Simple keyword search returning ScoredChunks."""
        import re

        def tokenize(text: str) -> set:
            """Tokenize text, stripping punctuation."""
            return set(re.findall(r"\b\w+\b", text.lower()))

        results: list[tuple[str, str, dict[str, Any], float]] = []
        query_words = tokenize(query)

        for _idx, (chunk_id, text, meta) in enumerate(zip(self._ids, self._texts, self._metadatas, strict=False)):
            text_words = tokenize(text)
            overlap = len(query_words & text_words)
            if overlap > 0:
                score = overlap / max(len(query_words), 1)
                results.append((chunk_id, text, meta, score))

        # Sort by score descending, then by chunk_id for determinism
        results.sort(key=lambda x: (-x[3], x[0]))

        return [ScoredChunk(chunk_id=cid, text=txt, score=sc, metadata=mt) for cid, txt, mt, sc in results[:top_k]]

    def __len__(self) -> int:
        return len(self._ids)


# --- LLM Adapters ---


class DummyLLMAdapter:
    """Dummy LLM adapter for testing."""

    def generate(self, prompt: str, context: str = "") -> str:
        """Return a dummy response."""
        return f"DummyLLM response for: {prompt[:50]}..."


class RagQA:
    """RAG Question-Answering system."""

    def __init__(
        self,
        index: InMemoryIndex | None = None,
        generator: DummyLLMAdapter | None = None,
    ):
        self.index = index or InMemoryIndex()
        self.generator = generator or DummyLLMAdapter()

    def index_documents(
        self,
        docs: list[Doc],
        chunked: bool = False,
        chunk_size: int = 100,
        overlap: int = 10,
    ) -> None:
        """Index documents for retrieval."""
        if chunked:
            self.index.add_documents_chunked(docs, chunk_size, overlap)
        else:
            self.index.add_documents(docs=docs)

    def answer(self, question: str, top_k: int = 3) -> dict[str, Any]:
        """Answer a question using RAG."""
        results = self.index.search(question, top_k=top_k)

        context_parts = []
        sources = []
        for chunk in results:
            context_parts.append(chunk.text)
            sources.append(
                {
                    "doc_id": chunk.chunk_id,
                    "score": chunk.score,
                    "metadata": chunk.metadata,
                }
            )

        context = "\n".join(context_parts)
        answer = self.generator.generate(question, context)

        return {
            "answer": answer,
            "sources": sources,
            "context": context,
        }


__all__ = [
    # Core types
    "ScoredChunk",
    "Doc",
    "BaseIndex",
    "BaseRetriever",
    "RetrievalResult",
    "InMemoryIndex",
    "RagQA",
    "DummyLLMAdapter",
    # Utility functions
    "to_scored_chunk",
    "normalize_results",
    # Re-exported from tools.rag
    *_EXPORTS,
]
