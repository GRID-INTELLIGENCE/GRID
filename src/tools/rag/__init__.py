"""
RAG (Retrieval-Augmented Generation) module for GRID.

Provides unified RAG system with:
- Local Ollama models (nomic-embed-text-v2, ministral, gpt-oss-safeguard)
- ChromaDB vector store for persistence
- Clean API for indexing and querying
- Single unified engine with multiple modes
"""

from .config import ModelMode, RAGConfig
from .embeddings import OllamaEmbeddingProvider, get_embedding_provider
from .engine import RAGEngine, create_conversational_engine, create_on_demand_engine, create_persistent_engine

# Backward compatibility exports
from .indexer import chunk_text, index_repository, read_file_content
from .llm import OllamaLocalLLM, get_llm_provider

# Lazy import model routing utilities – may fail during indexing due to circular imports
try:
    from .model_router import ModelRoutingDecision, route_models
except Exception as e:
    import logging

    logging.getLogger(__name__).warning(f"Model routing import failed: {e}")
    ModelRoutingDecision = None  # type: ignore
    route_models = None  # type: ignore

# Legacy exports for backward compatibility (aliases, not redefinitions)
OnDemandRAGEngine = create_on_demand_engine  # noqa: F811
PersistentRAGEngine = create_persistent_engine  # Legacy alias

# Optional ChromaDB dependency
try:
    from .vector_store import ChromaDBVectorStore
except ImportError:
    ChromaDBVectorStore = None  # type: ignore[misc,assignment]

# Optional LangChain integration
try:
    from .langchain import (
        # Agent
        ConversationalRAGAgent,
        # LangSmith
        configure_langsmith,
        create_conversational_agent,
        create_rag_agent,
        # Tools
        create_rag_tool,
        create_simple_rag_chain,
        is_tracing_enabled,
    )

    _langchain_available = True
except ImportError:
    # LangChain not installed
    create_rag_agent = None  # type: ignore[misc,assignment]
    create_simple_rag_chain = None  # type: ignore[misc,assignment]
    create_rag_tool = None  # type: ignore[misc,assignment]
    ConversationalRAGAgent = None  # type: ignore[misc,assignment]
    create_conversational_agent = None  # type: ignore[misc,assignment]
    configure_langsmith = None  # type: ignore[misc,assignment]
    is_tracing_enabled = None  # type: ignore[misc,assignment]
    _langchain_available = False

__all__ = [
    # Main unified engine
    "RAGEngine",
    "create_persistent_engine",
    "create_on_demand_engine",
    "create_conversational_engine",
    # Legacy compatibility
    "OnDemandRAGEngine",
    # Configuration
    "RAGConfig",
    "ModelMode",
    # Routing
    "ModelRoutingDecision",
    "route_models",
    # Embeddings
    "get_embedding_provider",
    "OllamaEmbeddingProvider",
    # LLM
    "get_llm_provider",
    "OllamaLocalLLM",
    # Vector Store
    "ChromaDBVectorStore",
    # Indexing utilities
    "index_repository",
    "chunk_text",
    "read_file_content",
    # LangChain integration (optional)
    "create_rag_agent",
    "create_simple_rag_chain",
    "create_rag_tool",
    "ConversationalRAGAgent",
    "create_conversational_agent",
    "configure_langsmith",
    "is_tracing_enabled",
]

__version__ = "2.1.0"
