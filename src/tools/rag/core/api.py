"""RAG API - Simple entry points for common RAG operations.

This module provides the main interfaces developers use for RAG functionality.
"""

from .engine import RAGEngine, create_persistent_engine, create_on_demand_engine, create_conversational_engine
from .config import RAGConfig


def query(question: str, mode: str = "persistent", **kwargs) -> dict:
    """Simple query interface.

    Args:
        question: The question to answer
        mode: 'persistent', 'on_demand', or 'conversational'
        **kwargs: Additional arguments passed to the engine

    Returns:
        Dict with answer, sources, and metadata
    """
    engine = RAGEngine(mode=mode)
    return engine.query(question, **kwargs)


def index_repository(repo_path: str, **kwargs) -> dict:
    """Index a repository for persistent queries.

    Args:
        repo_path: Path to the repository to index
        **kwargs: Additional indexing arguments

    Returns:
        Indexing statistics
    """
    engine = create_persistent_engine()
    return engine.index_repository(repo_path, **kwargs)


def chat(message: str, **kwargs) -> dict:
    """Conversational RAG interface.

    Args:
        message: User message
        **kwargs: Additional conversation arguments

    Returns:
        Dict with response and conversation state
    """
    engine = create_conversational_engine()
    return engine.query(message, **kwargs)


def get_stats() -> dict:
    """Get RAG system statistics."""
    engine = create_persistent_engine()
    return engine.get_stats()


# Quick setup functions
def setup_local_rag() -> RAGEngine:
    """Create a local RAG engine with default settings."""
    config = RAGConfig.from_env()
    return create_persistent_engine(config)


def setup_on_demand_rag() -> RAGEngine:
    """Create an on-demand RAG engine."""
    config = RAGConfig.from_env()
    return create_on_demand_engine(config)
