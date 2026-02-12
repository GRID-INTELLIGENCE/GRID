"""Vector store implementations for RAG and semantic search.

This module provides base interfaces and implementations for storing and
querying dense vectors (embeddings) for similarity search operations.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseEmbedding(ABC):
    """Base class for embedding models."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of embeddings produced by this model."""
        pass

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Embed a single text string.

        Args:
            text: The text to embed

        Returns:
            A list of floats representing the embedding
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts.

        Args:
            texts: A list of texts to embed

        Returns:
            A list of embedding vectors
        """
        pass


class SimpleEmbedding(BaseEmbedding):
    """Simple embedding implementation for debugging."""

    def __init__(self, embedding_dim: int = 384) -> None:
        """Initialize the simple embedding.

        Args:
            embedding_dim: Dimension of embeddings (default: 384)
        """
        self._embedding_dim = embedding_dim

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._embedding_dim

    def embed(self, text: str) -> list[float]:
        """Create a simple deterministic embedding from text hash."""
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)

        # Generate deterministic values based on hash
        embeddings = []
        for i in range(self._embedding_dim):
            # Create pseudo-random but deterministic values
            val = ((hash_int + i) % 10000) / 10000.0
            embeddings.append(val * 2.0 - 1.0)  # Scale to [-1, 1]

        return embeddings

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts."""
        return [self.embed(text) for text in texts]


class DenseVectorStore(ABC):
    """Base class for dense vector stores."""

    @property
    @abstractmethod
    def embedding(self) -> BaseEmbedding:
        """Return the embedding model used by this store."""
        pass

    @abstractmethod
    def add(self, doc_id: str, vector: list[float], metadata: dict[str, Any] | None = None) -> None:
        """Add a vector to the store.

        Args:
            doc_id: Unique identifier for the document
            vector: The embedding vector
            metadata: Optional metadata associated with the vector
        """
        pass

    @abstractmethod
    def query(self, vector: list[float], k: int = 10) -> list[tuple[str, float]]:
        """Query the store for similar vectors.

        Args:
            vector: The query vector
            k: Number of results to return

        Returns:
            A list of (doc_id, similarity_score) tuples
        """
        pass

    @abstractmethod
    def delete(self, doc_id: str) -> None:
        """Delete a vector from the store.

        Args:
            doc_id: The document ID to delete
        """
        pass


class InMemoryDenseVectorStore(DenseVectorStore):
    """In-memory implementation of dense vector store."""

    def __init__(self, embedding_dim: int = 384) -> None:
        """Initialize the in-memory vector store.

        Args:
            embedding_dim: Dimension of embeddings (default: 384)
        """
        self._vectors: dict[str, Any] = {}
        self._embedding = SimpleEmbedding(embedding_dim=embedding_dim)

    @property
    def embedding(self) -> BaseEmbedding:
        """Return the embedding model."""
        return self._embedding

    def add(self, doc_id: str, vector: list[float], metadata: dict[str, Any] | None = None) -> None:
        """Add a vector to the store."""
        self._vectors[doc_id] = {
            "vector": vector,
            "metadata": metadata or {},
        }

    def query(self, vector: list[float], k: int = 10) -> list[tuple[str, float]]:
        """Query the store for similar vectors using cosine similarity."""
        import math

        def cosine_similarity(a: list[float], b: list[float]) -> float:
            """Calculate cosine similarity between two vectors."""
            dot_product = sum(x * y for x, y in zip(a, b, strict=False))
            mag_a = math.sqrt(sum(x * x for x in a))
            mag_b = math.sqrt(sum(x * x for x in b))

            if mag_a == 0 or mag_b == 0:
                return 0.0

            return dot_product / (mag_a * mag_b)

        # Calculate similarity to all stored vectors
        results = []
        for doc_id, data in self._vectors.items():
            similarity = cosine_similarity(vector, data["vector"])
            results.append((doc_id, similarity))

        # Sort by similarity (descending) and return top k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]

    def delete(self, doc_id: str) -> None:
        """Delete a vector from the store."""
        if doc_id in self._vectors:
            del self._vectors[doc_id]


class ChromaDenseVectorStore(DenseVectorStore):
    """ChromaDB implementation of dense vector store."""

    def __init__(self, embedding_dim: int = 384) -> None:
        """Initialize the ChromaDB vector store.

        Args:
            embedding_dim: Dimension of embeddings (default: 384)
        """
        try:
            import chromadb
            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(
                name="grid_embeddings",
                metadata={"hnsw:space": "cosine"}
            )
        except ImportError:
            raise ImportError("chromadb is required for ChromaDenseVectorStore")

        self._embedding = SimpleEmbedding(embedding_dim=embedding_dim)

    @property
    def embedding(self) -> BaseEmbedding:
        """Return the embedding model."""
        return self._embedding

    def add(self, doc_id: str, vector: list[float], metadata: dict[str, Any] | None = None) -> None:
        """Add a vector to the store."""
        self._collection.upsert(
            ids=[doc_id],
            embeddings=[vector],
            metadatas=[metadata or {}],
        )

    def query(self, vector: list[float], k: int = 10) -> list[tuple[str, float]]:
        """Query the store for similar vectors."""
        results = self._collection.query(
            query_embeddings=[vector],
            n_results=k,
        )

        # Transform Chroma results to our format
        doc_ids = results["ids"][0]
        distances = results["distances"][0]

        # Convert distances to similarity (assuming Chroma uses L2 distance)
        # For cosine similarity, ChromaDB with cosine space returns distance
        # which is 1 - similarity, so we convert back
        similarities = [1.0 - d for d in distances]

        return list(zip(doc_ids, similarities, strict=False))

    def delete(self, doc_id: str) -> None:
        """Delete a vector from the store."""
        self._collection.delete(ids=[doc_id])


class VectorStoreFactory:
    """Factory for creating vector store instances."""

    @staticmethod
    def create_vector_store(
        store_type: str,
        embedding_dim: int = 384,
        **kwargs: Any,
    ) -> DenseVectorStore:
        """Create a vector store of the given type.

        Args:
            store_type: The type of store to create ("in_memory" or "chroma")
            embedding_dim: Dimension of embeddings (default: 384)
            **kwargs: Additional arguments to pass to the store

        Returns:
            The created vector store

        Raises:
            ValueError: If store_type is not supported
        """
        if store_type == "in_memory":
            return InMemoryDenseVectorStore(embedding_dim=embedding_dim)
        elif store_type == "chroma":
            return ChromaDenseVectorStore(embedding_dim=embedding_dim)
        else:
            raise ValueError(f"Unknown vector store type: {store_type}")
