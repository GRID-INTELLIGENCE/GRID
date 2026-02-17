"""Type definitions and protocols for RAG components."""

from typing import Any, Protocol


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""

    def embed(self, text: str) -> dict[str, float]:
        """Convert text to embedding vector as sparse dict."""
        ...

    def embed_batch(self, texts: list[str]) -> list[dict[str, float]]:
        """Convert list of texts to embeddings."""
        ...

    async def async_embed(self, text: str) -> dict[str, float]:
        """Convert text to embedding vector as sparse dict (async)."""
        ...

    async def async_embed_batch(self, texts: list[str]) -> list[dict[str, float]]:
        """Convert list of texts to embeddings (async)."""
        ...


class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text completion."""
        ...

    async def async_generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text completion (async)."""
        ...


class Document:
    """Represents a document with metadata."""

    def __init__(
        self,
        id: str,
        text: str | None = None,
        metadata: dict[str, Any] | None = None,
        content: str | None = None,
    ):
        self.id = id
        self.text = text or content or ""
        self.metadata = metadata or {}

    @property
    def content(self) -> str:
        """Alias for text for backward compatibility."""
        return self.text

    @content.setter
    def content(self, value: str) -> None:
        self.text = value

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {"id": self.id, "text": self.text, "metadata": self.metadata}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Document":
        """Create from dictionary representation."""
        return cls(data["id"], data["text"], data.get("metadata", {}))


class Chunk:
    """Represents a chunk of a document."""

    def __init__(
        self,
        id: str,
        text: str | None = None,
        doc_id: str = "",
        metadata: dict[str, Any] | None = None,
        content: str | None = None,
    ):
        self.id = id
        self.text = text or content or ""
        self.doc_id = doc_id
        self.metadata = metadata or {}

    @property
    def content(self) -> str:
        """Alias for text for backward compatibility."""
        return self.text

    @content.setter
    def content(self, value: str) -> None:
        self.text = value

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {"id": self.id, "text": self.text, "doc_id": self.doc_id, "metadata": self.metadata}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Chunk":
        """Create from dictionary representation."""
        return cls(data["id"], data["text"], data["doc_id"], data.get("metadata", {}))


class VectorStoreConfig:
    """Configuration for vector store."""

    def __init__(self, similarity_threshold: float = 0.0, max_results: int = 10, include_metadata: bool = True):
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
        self.include_metadata = include_metadata


class ScoredChunk(Chunk):
    """Chunk with similarity score."""

    def __init__(self, id: str, text: str, doc_id: str, score: float, metadata: dict[str, Any] | None = None):
        super().__init__(id, text, doc_id, metadata)
        self.score = score

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        d = super().to_dict()
        d["score"] = self.score
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScoredChunk":
        """Create from dictionary representation."""
        return cls(data["id"], data["text"], data["doc_id"], data["score"], data.get("metadata", {}))
