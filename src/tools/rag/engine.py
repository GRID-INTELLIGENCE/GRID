"""Engine compatibility shim.

Re-exports RAG engine classes and factory functions from their implementation modules.
This module exists for backward compatibility with imports expecting 'engine.py'.
"""

from .on_demand_engine import OnDemandRAGEngine, OnDemandRAGResult, RAGHooks
from .rag_engine import RAGEngine

__all__ = [
    "RAGEngine",
    "OnDemandRAGEngine",
    "OnDemandRAGResult",
    "RAGHooks",
    "create_persistent_engine",
    "create_on_demand_engine",
    "create_conversational_engine",
]


def create_persistent_engine(
    collection_name: str = "grid_knowledge",
    persist_directory: str | None = None,
    **kwargs,
) -> RAGEngine:
    """Create a RAG engine with persistent ChromaDB storage.

    Args:
        collection_name: Name of the ChromaDB collection
        persist_directory: Directory for ChromaDB persistence
        **kwargs: Additional arguments passed to RAGEngine

    Returns:
        Configured RAGEngine instance
    """
    from .config import RAGConfig

    config = RAGConfig.from_env()
    config.collection_name = collection_name
    if persist_directory:
        config.vector_store_path = persist_directory

    return RAGEngine(config=config)


def create_on_demand_engine(
    docs_root: str = "docs",
    repo_root: str = ".",
    hooks: RAGHooks | None = None,
    **kwargs,
) -> OnDemandRAGEngine:
    """Create an on-demand RAG engine for query-time indexing.

    Args:
        docs_root: Root directory for documentation
        repo_root: Root directory of the repository
        hooks: Optional callbacks for engine events
        **kwargs: Additional arguments passed to OnDemandRAGEngine

    Returns:
        Configured OnDemandRAGEngine instance
    """
    from .config import RAGConfig

    config = RAGConfig.from_env()
    return OnDemandRAGEngine(
        config=config,
        docs_root=docs_root,
        repo_root=repo_root,
        hooks=hooks,
    )


def create_conversational_engine(
    collection_name: str = "grid_conversations",
    persist_directory: str | None = None,
    **kwargs,
) -> RAGEngine:
    """Create a RAG engine optimized for conversational interactions.

    This is a variant of the persistent engine with settings tuned for
    multi-turn conversations and context retention.

    Args:
        collection_name: Name of the ChromaDB collection
        persist_directory: Directory for ChromaDB persistence
        **kwargs: Additional arguments passed to RAGEngine

    Returns:
        Configured RAGEngine instance for conversations
    """
    from .config import RAGConfig

    config = RAGConfig.from_env()
    config.collection_name = collection_name
    if persist_directory:
        config.vector_store_path = persist_directory

    # Conversational settings
    config.top_k = kwargs.get("top_k", 5)  # More context for conversations

    return RAGEngine(config=config)
