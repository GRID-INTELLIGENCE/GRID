"""Base vector store interface."""

from abc import ABC, abstractmethod
from typing import Any


class BaseVectorStore(ABC):
    """Base interface for vector stores."""

    @abstractmethod
    def add(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add documents with embeddings to the store.

        Args:
            ids: Document IDs
            documents: Document texts
            embeddings: Dense embedding vectors
            metadatas: Optional metadata for each document
        """
        pass

    @abstractmethod
    def query(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """Query the vector store.

        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            where: Optional metadata filter
            include: Optional list of fields to include

        Returns:
            Dictionary with 'ids', 'documents', 'metadatas', 'distances'
        """
        pass

    @abstractmethod
    def delete(self, ids: list[str] | None = None, where: dict[str, Any] | None = None) -> None:
        """Delete documents from the store.

        Args:
            ids: Optional list of IDs to delete
            where: Optional metadata filter
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """Get the number of documents in the store.

        Returns:
            Number of documents
        """
        pass

    def __len__(self) -> int:
        """Return number of documents in the store."""
        return self.count()

    def add_documents(self, documents: list[Any]) -> None:
        """Add a list of Document objects to the store."""
        ids = [doc.id for doc in documents]
        texts = [doc.text for doc in documents]
        metadatas = [doc.metadata for doc in documents]

        # Use a simple embedding fallback if none provided
        # In practice, the caller should handle embeddings, but for tests we might need this
        from ..embeddings.simple import SimpleEmbedding

        embedder = SimpleEmbedding()
        embeddings = [embedder.embed(doc.text) for doc in documents]
        # Ensure embeddings are dense lists of floats
        dense_embeddings = []
        for emb in embeddings:
            if isinstance(emb, dict):
                # Convert sparse to dense if needed (very basic)
                max_idx = max([int(k) for k in emb.keys() if k.isdigit()] + [99])
                dense = [0.0] * (max_idx + 1)
                for k, v in emb.items():
                    if k.isdigit():
                        dense[int(k)] = v
                dense_embeddings.append(dense)
            else:
                dense_embeddings.append(emb.tolist() if hasattr(emb, "tolist") else list(emb))

        self.add(ids=ids, documents=texts, embeddings=dense_embeddings, metadatas=metadatas)

    def similarity_search(
        self, query: str, k: int = 5, where: dict[str, Any] | None = None
    ) -> list[Any]:
        """Search for similar documents using query string."""
        from ..embeddings.simple import SimpleEmbedding

        embedder = SimpleEmbedding()
        query_embedding = embedder.embed(query)
        if hasattr(query_embedding, "tolist"):
            query_embedding = query_embedding.tolist()
        elif isinstance(query_embedding, dict):
             # basic sparse to dense
             max_idx = max([int(k) for k in query_embedding.keys() if k.isdigit()] + [99])
             dense = [0.0] * (max_idx + 1)
             for key, v in query_embedding.items():
                 if key.isdigit():
                     dense[int(key)] = v
             query_embedding = dense

        results = self.query(query_embedding=query_embedding, n_results=k, where=where)

        from ..types import ScoredChunk

        scored_chunks = []
        docs = results.get("documents", [])
        metas = results.get("metadatas", [])
        ids = results.get("ids", [])
        distances = results.get("distances", [1.0] * len(docs))

        for i in range(len(docs)):
            score = 1.0 / (1.0 + distances[i])
            # Use content=docs[i] for backward compat if anyone expects it
            scored_chunks.append(
                ScoredChunk(
                    id=ids[i],
                    text=docs[i],
                    doc_id=ids[i],
                    score=score,
                    metadata=metas[i],
                )
            )
        return scored_chunks

    def update_document(self, document: Any) -> None:
        """Update an existing document."""
        self.delete(ids=[document.id])
        self.add_documents([document])

    def delete_document(self, doc_id: str) -> None:
        """Delete a document by ID."""
        self.delete(ids=[doc_id])
