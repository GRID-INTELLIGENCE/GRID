"""In-memory vector store for document retrieval.

Security Note:
    This module uses pickle for serialization. Pickle files should ONLY be loaded
    from trusted sources as pickle deserialization can execute arbitrary code.
    For untrusted data, use the JSON format instead.
"""

import json
import logging
import math
from typing import Any

from .types import LLMProvider, VectorStoreConfig

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when a security validation fails."""

    pass


# Security: Define allowed directories for pickle loading
_ALLOWED_PICKLE_DIRS: set[str] = {
    ".rag_db",
    ".cache",
    "src/.rag_db",
}


class VectorStore:
    """In-memory vector store with similarity search."""

    def __init__(self, config: VectorStoreConfig | None = None):
        self.config = config or VectorStoreConfig()
        self.docs: list[str] = []
        self.embeddings: list[dict[str, float]] = []
        self.metadatas: list[dict[str, Any]] = []
        self.ids: list[str] = []

    def add(
        self,
        ids: list[str],
        docs: list[str],
        embeddings: list[dict[str, float]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add documents with embeddings to the store."""
        if not (len(ids) == len(docs) == len(embeddings)):
            raise ValueError("ids, docs, and embeddings must have same length")

        if metadatas is None:
            metadatas = [{}] * len(docs)
        elif len(metadatas) != len(docs):
            raise ValueError("metadatas must have same length as docs")

        self.ids.extend(ids)
        self.docs.extend(docs)
        self.embeddings.extend(embeddings)
        self.metadatas.extend(metadatas)

    def _cosine_similarity(self, vec1: dict[str, float], vec2: dict[str, float]) -> float:
        """Calculate cosine similarity between two sparse vectors."""
        # Get union of keys
        keys = set(vec1.keys()) | set(vec2.keys())

        # Calculate dot product
        dot_product = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in keys)

        # Calculate magnitudes
        mag1 = math.sqrt(sum(v * v for v in vec1.values()))
        mag2 = math.sqrt(sum(v * v for v in vec2.values()))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    def query(
        self, query_embedding: dict[str, float], k: int = 5, threshold: float | None = None
    ) -> tuple[list[str], list[dict[str, Any]], list[float]]:
        """Query for similar documents."""
        if k > len(self.docs):
            k = len(self.docs)

        threshold = threshold or self.config.similarity_threshold

        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(self.embeddings):
            sim = self._cosine_similarity(query_embedding, doc_embedding)
            if sim >= threshold:
                similarities.append((i, sim))

        # Sort by similarity and take top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        similarities = similarities[:k]

        # Extract results
        docs = []
        metadatas = []
        scores = []

        for idx, score in similarities:
            docs.append(self.docs[idx])
            metadatas.append(self.metadatas[idx] if self.config.include_metadata else {})
            scores.append(score)

        return docs, metadatas, scores

    def query_with_llm(self, query: str, llm: LLMProvider, k: int = 3, context_template: str | None = None) -> str:
        """Query and generate answer using LLM."""
        # For now, use a simple embedding approach
        # In a real implementation, you'd embed the query
        query_embedding = self._simple_embed(query)

        # Retrieve relevant docs
        docs, metadatas, scores = self.query(query_embedding, k=k)

        if not docs:
            return "No relevant information found."

        # Build context
        if context_template is None:
            context_template = """Context:
{context}

Question: {question}

Answer:"""

        context = "\n\n".join(f"[{i + 1}] {doc}" for i, doc in enumerate(docs))
        prompt = context_template.format(context=context, question=query)

        # Generate answer
        return llm.generate(prompt)

    def _simple_embed(self, text: str) -> dict[str, float]:
        """Simple fallback embedding using word frequencies."""
        words = text.lower().split()
        return {word: words.count(word) for word in set(words)}

    def save(self, path: str) -> None:
        """Save store to file using JSON format (secure)."""
        if not path.endswith(".json"):
            raise ValueError("Security: Only JSON format is supported. Use .json extension")

        # Convert to NDJSON format with config header
        lines = [
            json.dumps(
                {
                    "type": "config",
                    "similarity_threshold": self.config.similarity_threshold,
                    "max_results": self.config.max_results,
                    "include_metadata": self.config.include_metadata,
                }
            )
        ]

        lines.extend(
                json.dumps(
                    {
                        "type": "document",
                        "id": self.ids[i],
                        "doc": self.docs[i],
                        "embedding": self.embeddings[i],
                        "metadata": self.metadatas[i],
                    }
                )
            for i in range(len(self.ids))
        )
        with open(path, "w") as f:
            f.write("\n".join(lines))

    @classmethod
    def load(cls, path: str) -> "VectorStore":
        """Load store from JSON file (secure)."""
        if not path.endswith(".json"):
            raise ValueError("Security: Only JSON format is supported. Use .json extension")

        with open(path) as f:
            lines = f.readlines()

        store = cls()
        config_loaded = False

        for line in lines:
            if not line.strip():
                continue

            data = json.loads(line)

            if data.get("type") == "config":
                # Load configuration
                store.config = VectorStoreConfig(
                    similarity_threshold=data.get("similarity_threshold", 0.0),
                    max_results=data.get("max_results", 10),
                    include_metadata=data.get("include_metadata", True),
                )
                config_loaded = True
            elif data.get("type") == "document":
                # Load document data
                store.ids.append(data["id"])
                store.docs.append(data["doc"])
                store.embeddings.append(data["embedding"])
                store.metadatas.append(data["metadata"])

        if not config_loaded:
            # Use default config if not found
            store.config = VectorStoreConfig()

        return store

    def to_ndjson(self) -> list[str]:
        """Convert to NDJSON format."""
        lines = [
                json.dumps(
                    {
                        "id": self.ids[i],
                        "doc": self.docs[i],
                        "embedding": self.embeddings[i],
                        "metadata": self.metadatas[i],
                    }
                )
            for i in range(len(self.ids))
        ]
        return lines

    @classmethod
    def from_ndjson(cls, lines: list[str]) -> "VectorStore":
        """Create from NDJSON format."""
        store = cls()
        for line in lines:
            if line.strip():
                data = json.loads(line)
                store.ids.append(data["id"])
                store.docs.append(data["doc"])
                store.embeddings.append(data["embedding"])
                store.metadatas.append(data["metadata"])
        return store

    def __len__(self) -> int:
        """Return number of documents in store."""
        return len(self.docs)

    def clear(self) -> None:
        """Clear all documents from store."""
        self.docs.clear()
        self.embeddings.clear()
        self.metadatas.clear()
        self.ids.clear()
