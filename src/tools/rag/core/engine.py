"""Unified RAG Engine - Single entry point for all RAG operations.

Combines persistent indexing, on-demand querying, and conversational features.
"""

import logging
from pathlib import Path
from typing import Any

from .config import RAGConfig
from .embeddings.factory import get_embedding_provider
from .indexer import chunk_text, index_repository, read_file_content
from .llm.factory import get_llm_provider
from .utils import check_ollama_connection
from .vector_store.base import BaseVectorStore

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    from .vector_store.chromadb_store import ChromaDBVectorStore
except ImportError:
    ChromaDBVectorStore = None

try:
    from .vector_store.databricks_store import DatabricksVectorStore
except ImportError:
    DatabricksVectorStore = None


class RAGEngine:
    """Unified RAG engine supporting multiple modes.

    Modes:
    - persistent: Pre-indexed knowledge base (fast queries)
    - on_demand: Query-time indexing (flexible, slower)
    - conversational: Multi-turn conversations with memory
    """

    def __init__(self, config: RAGConfig | None = None, mode: str = "persistent"):
        """Initialize RAG engine.

        Args:
            config: RAG configuration
            mode: 'persistent', 'on_demand', or 'conversational'
        """
        if config is None:
            config = RAGConfig.from_env()

        # Ensure local-only operation
        config.ensure_local_only()

        # Validate Ollama connection
        if not check_ollama_connection(config.ollama_base_url):
            if config.embedding_provider == "ollama":
                raise RuntimeError(f"Ollama required but not running at {config.ollama_base_url}")

        self.config = config
        self.mode = mode
        self.embedding_provider = get_embedding_provider(config=config)
        self.llm_provider = get_llm_provider(config=config)
        self.vector_store: BaseVectorStore | None = None
        self.conversation_history = []

        if mode == "persistent":
            self._init_persistent_store()
        elif mode == "conversational":
            self._init_persistent_store()  # Conversational needs persistence for memory

    def _init_persistent_store(self):
        """Initialize persistent vector store."""
        from .vector_store.registry import VectorStoreRegistry

        provider = self.config.vector_store_provider.lower()
        try:
            if provider == "databricks":
                self.vector_store = VectorStoreRegistry.create(
                    provider,
                    chunk_table=self.config.databricks_chunk_table,
                    document_table=self.config.databricks_document_table,
                    schema=self.config.databricks_schema,
                )
            elif provider == "chromadb":
                self.vector_store = VectorStoreRegistry.create(
                    provider,
                    collection_name=self.config.collection_name,
                    persist_directory=self.config.vector_store_path,
                )
            elif provider == "in_memory":
                self.vector_store = VectorStoreRegistry.create(provider)
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise

    def index_repository(self, repo_path: str, **kwargs) -> dict[str, Any]:
        """Index a repository for persistent queries."""
        if self.mode != "persistent":
            raise ValueError("Repository indexing only available in persistent mode")

        return index_repository(repo_path, config=self.config, **kwargs)

    def query(self, question: str, **kwargs) -> dict[str, Any]:
        """Query the knowledge base."""
        if self.mode == "persistent":
            return self._query_persistent(question, **kwargs)
        elif self.mode == "on_demand":
            return self._query_on_demand(question, **kwargs)
        elif self.mode == "conversational":
            return self._query_conversational(question, **kwargs)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def _query_persistent(self, question: str, **kwargs) -> dict[str, Any]:
        """Query pre-indexed knowledge base."""
        if not self.vector_store:
            raise RuntimeError("Vector store not initialized")

        # Generate embedding
        query_embedding = self.embedding_provider.embed(question)

        # Retrieve documents
        results = self.vector_store.query(query_embedding=query_embedding, n_results=self.config.top_k)

        # Generate answer
        context = "\n".join(results["documents"])
        prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"

        answer = self.llm_provider.generate(prompt)

        return {"answer": answer, "sources": results["documents"], "metadata": results["metadatas"]}

    def _query_on_demand(self, question: str, docs_root: str = "docs", **kwargs) -> dict[str, Any]:
        """Query with on-demand indexing."""
        from .vector_store import InMemoryDenseVectorStore

        # Find and read relevant files
        docs_path = Path(docs_root)
        if not docs_path.exists():
            raise FileNotFoundError(f"Docs directory not found: {docs_root}")

        files = list(docs_path.rglob("*.md")) + list(docs_path.rglob("*.txt"))
        if not files:
            raise ValueError(f"No documentation files found in {docs_root}")

        # Read and chunk content
        documents = []
        for file_path in files[:10]:  # Limit for performance
            content = read_file_content(str(file_path))
            chunks = chunk_text(content, chunk_size=self.config.chunk_size)
            documents.extend(chunks)

        # Create temporary vector store
        temp_store = InMemoryDenseVectorStore()
        embeddings = [self.embedding_provider.embed(doc) for doc in documents]
        temp_store.add(ids=[f"chunk_{i}" for i in range(len(documents))], documents=documents, embeddings=embeddings)

        # Query
        query_embedding = self.embedding_provider.embed(question)
        results = temp_store.query(query_embedding=query_embedding, n_results=5)

        # Generate answer
        context = "\n".join(results["documents"])
        prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        answer = self.llm_provider.generate(prompt)

        return {
            "answer": answer,
            "sources": results["documents"],
            "file_count": len(files),
            "chunk_count": len(documents),
        }

    def _query_conversational(self, question: str, **kwargs) -> dict[str, Any]:
        """Query with conversation memory."""
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": question})

        # Create context from recent conversation
        context_window = self.conversation_history[-6:]  # Last 3 exchanges
        conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context_window])

        # Query with conversation context
        full_query = f"Conversation:\n{conversation_context}\n\nCurrent question: {question}"

        result = self._query_persistent(full_query, **kwargs)

        # Add response to history
        self.conversation_history.append({"role": "assistant", "content": result["answer"]})

        result["conversation_length"] = len(self.conversation_history)
        return result

    def clear_conversation(self):
        """Clear conversation history."""
        self.conversation_history = []

    def get_stats(self) -> dict[str, Any]:
        """Get engine statistics."""
        return {
            "mode": self.mode,
            "config": {
                "embedding_provider": self.config.embedding_provider,
                "llm_provider": self.config.llm_mode.value,
                "vector_store": self.config.vector_store_provider,
                "collection_name": self.config.collection_name,
            },
            "conversation_turns": len(self.conversation_history) if self.mode == "conversational" else 0,
            "vector_store_count": self.vector_store.count() if self.vector_store else 0,
        }


# Convenience functions for backward compatibility
def create_persistent_engine(config: RAGConfig | None = None) -> RAGEngine:
    """Create persistent RAG engine (replaces old RAGEngine)."""
    return RAGEngine(config, mode="persistent")


def create_on_demand_engine(config: RAGConfig | None = None) -> RAGEngine:
    """Create on-demand RAG engine (replaces old OnDemandRAGEngine)."""
    return RAGEngine(config, mode="on_demand")


def create_conversational_engine(config: RAGConfig | None = None) -> RAGEngine:
    """Create conversational RAG engine (replaces old ConversationalRAGEngine)."""
    return RAGEngine(config, mode="conversational")
