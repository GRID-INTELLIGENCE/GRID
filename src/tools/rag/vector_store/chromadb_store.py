"""ChromaDB vector store implementation."""

from typing import Any, cast

import chromadb
from chromadb.config import Settings

from .base import BaseVectorStore


class ChromaDBVectorStore(BaseVectorStore):
    """ChromaDB-based vector store with proper dense embeddings.

    Uses ChromaDB for persistence and efficient similarity search.
    """

    def __init__(
        self,
        collection_name: str = "grid_knowledge_base",
        persist_directory: str = ".rag_db",
        embedding_function: Any | None = None,
    ) -> None:
        """Initialize ChromaDB vector store.

        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist data
            embedding_function: Optional embedding function (for ChromaDB's built-in)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory, settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )

        # Get or create collection
        # Note: We'll handle embeddings ourselves, so we don't pass embedding_function
        # to the collection - we'll add pre-computed embeddings
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception:
            # Collection doesn't exist, create it
            # We'll use add with embeddings directly
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},  # Use cosine similarity
            )

    def clear(self) -> None:
        """Clear all documents from the collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception:
            # Collection may not exist, just create a new one
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    def add(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add documents with embeddings to ChromaDB.

        Args:
            ids: Document IDs
            documents: Document texts
            embeddings: Dense embedding vectors
            metadatas: Optional metadata for each document
        """
        if not (len(ids) == len(documents) == len(embeddings)):
            raise ValueError("ids, documents, and embeddings must have same length")

        if metadatas is None:
            metadatas = [{"source": "rag_engine"}] * len(documents)
        elif len(metadatas) != len(documents):
            raise ValueError("metadatas must have same length as documents")

        # ChromaDB expects embeddings as list of lists
        self.collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """Query ChromaDB with embedding.

        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            where: Optional metadata filter
            include: Optional list of fields to include (default: all)

        Returns:
            Dictionary with 'ids', 'documents', 'metadatas', 'distances'
        """
        if include is None:
            include = ["documents", "metadatas", "distances"]

        results = self.collection.query(
            query_embeddings=[query_embedding], n_results=n_results, where=where, include=include
        )

        # ChromaDB returns lists of lists (one per query), so we extract first result
        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
        }

    def delete(self, ids: list[str] | None = None, where: dict[str, Any] | None = None) -> None:
        """Delete documents from ChromaDB.

        Args:
            ids: Optional list of IDs to delete
            where: Optional metadata filter
        """
        if ids:
            self.collection.delete(ids=ids)
        elif where:
            self.collection.delete(where=where)
        else:
            raise ValueError("Must provide either ids or where filter")

    def count(self) -> int:
        """Get the number of documents in the collection.

        Returns:
            Number of documents
        """
        return cast(int, self.collection.count())

    def reset(self) -> None:
        """Reset the collection (delete all documents)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name, metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            print(f"Warning: Could not reset collection {self.collection_name}: {e}")

    def _ensure_collection(self) -> None:
        """Ensure the collection exists, re-opening it if needed."""
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    def get_dimension(self) -> int:
        """Get the dimension of embeddings in the collection."""
        try:
            peek = self.collection.peek(limit=1)
            if peek and peek["embeddings"] and len(peek["embeddings"]) > 0:
                # ChromaDB returns embeddings as a list or numpy array
                emb = peek["embeddings"][0]
                return len(emb)
            return 0
        except Exception:
            return 0
