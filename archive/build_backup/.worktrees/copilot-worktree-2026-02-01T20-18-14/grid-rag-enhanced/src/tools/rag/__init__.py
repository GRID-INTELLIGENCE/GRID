"""
RAG (Retrieval-Augmented Generation) module for GRID.

Provides unified RAG system with:
- Local Ollama models (nomic-embed-text-v2, ministral, gpt-oss-safeguard)
- ChromaDB vector store for persistence
- Clean API for indexing and querying
"""

from .config import ModelMode, RAGConfig
from .embeddings import OllamaEmbeddingProvider, get_embedding_provider

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
from .on_demand_engine import OnDemandRAGEngine
from .rag_engine import RAGEngine

# Optional ChromaDB dependency
try:
    from .vector_store import ChromaDBVectorStore
except ImportError:
    ChromaDBVectorStore = None  # type: ignore[misc,assignment]

__all__ = [
    # Main engine
    "RAGEngine",
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
]

__version__ = "2.0.0"
