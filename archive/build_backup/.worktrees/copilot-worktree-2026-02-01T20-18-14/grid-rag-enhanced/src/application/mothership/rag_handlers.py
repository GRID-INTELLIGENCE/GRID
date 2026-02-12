"""
RAG Handlers Registration Module

Registers RAG-related handlers in the Ghost Registry for enhanced capabilities.
"""

import logging
from typing import Any

from application.mothership.api_core import ghost_registry, register_handler
from tools.rag.conversational_rag import ConversationalRAGEngine, create_conversational_rag_engine

logger = logging.getLogger(__name__)

# Global RAG engine instance
_rag_engine: ConversationalRAGEngine | None = None


def get_rag_engine() -> ConversationalRAGEngine:
    """Get or create the global RAG engine."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = create_conversational_rag_engine()
    return _rag_engine


@register_handler(
    "rag.query.conversational",
    description="Execute conversational RAG query with memory and multi-hop reasoning",
    tags=["rag", "query", "conversational"],
)
async def handle_conversational_query(
    query: str,
    session_id: str | None = None,
    enable_multi_hop: bool = False,
    temperature: float = 0.7,
    **kwargs: Any,
) -> dict[str, Any]:
    """Handle conversational RAG query."""
    engine = get_rag_engine()

    result = await engine.query(
        query_text=query,
        session_id=session_id,
        enable_multi_hop=enable_multi_hop,
        temperature=temperature,
    )

    return {
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "conversation_metadata": result.get("conversation_metadata", {}),
        "multi_hop_used": result.get("multi_hop_used", False),
        "fallback_used": result.get("fallback_used", False),
        "latency_ms": result.get("latency_ms", 0),
    }


@register_handler(
    "rag.session.create",
    description="Create a new RAG conversation session",
    tags=["rag", "session", "management"],
)
async def handle_create_session(
    session_id: str,
    metadata: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Handle session creation."""
    engine = get_rag_engine()

    engine.create_session(session_id, metadata or {})

    session_info = engine.get_session_info(session_id)

    return {
        "session_id": session_id,
        "created": True,
        "session_info": session_info,
    }


@register_handler(
    "rag.session.get",
    description="Get information about a RAG session",
    tags=["rag", "session", "management"],
)
async def handle_get_session(
    session_id: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Handle session retrieval."""
    engine = get_rag_engine()

    session_info = engine.get_session_info(session_id)

    if not session_info:
        return {
            "session_id": session_id,
            "found": False,
        }

    return {
        "session_id": session_id,
        "found": True,
        "session_info": session_info,
    }


@register_handler(
    "rag.session.delete",
    description="Delete a RAG conversation session",
    tags=["rag", "session", "management"],
)
async def handle_delete_session(
    session_id: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Handle session deletion."""
    engine = get_rag_engine()

    success = engine.delete_session(session_id)

    return {
        "session_id": session_id,
        "deleted": success,
    }


@register_handler(
    "rag.stats",
    description="Get RAG system statistics",
    tags=["rag", "stats", "monitoring"],
)
async def handle_get_stats(**kwargs: Any) -> dict[str, Any]:
    """Handle statistics retrieval."""
    engine = get_rag_engine()

    stats = engine.get_conversation_stats()

    return {
        "stats": stats,
        "system": "grid-rag-enhanced",
        "version": "2.0.0",
    }


@register_handler(
    "rag.index",
    description="Index documents for RAG",
    tags=["rag", "indexing", "documents"],
)
async def handle_index_documents(
    path: str,
    rebuild: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Handle document indexing."""
    engine = get_rag_engine()

    await engine.index(path, rebuild=rebuild)

    stats = engine.get_stats()

    return {
        "path": path,
        "indexed": True,
        "document_count": stats.get("document_count", 0),
    }


def register_rag_handlers() -> int:
    """Register all RAG handlers in the Ghost Registry.

    Returns:
        Number of handlers registered
    """
    # Import this module to trigger decorator registration

    # Count registered handlers
    registry = ghost_registry
    handlers = registry.list_handlers(tag="rag")

    count = len(handlers)
    logger.info(f"Registered {count} RAG handlers in Ghost Registry")

    return count


if __name__ == "__main__":
    # Test handler registration
    count = register_rag_handlers()
    print(f"Registered {count} RAG handlers")
