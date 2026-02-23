"""
Skill: rag.query_knowledge

Query GRID's project knowledge base using the RAG system.
Retrieves relevant documentation and provides LLM-generated answers.
"""

from __future__ import annotations

import asyncio
import inspect
import sys
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# Add grid root to path
grid_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(grid_root))

from .base import SimpleSkill

# Import bridge after path is set
try:
    from grid.integration.tools_bridge import get_tools_bridge

    _BRIDGE_AVAILABLE = True
except ImportError:
    _BRIDGE_AVAILABLE = False


def _resolve_awaitable(value: Any) -> Any:
    """Resolve awaitables in sync code paths (also when loop is already running)."""
    if not inspect.isawaitable(value):
        return value

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(value)

    output: dict[str, Any] = {}
    error: dict[str, BaseException] = {}

    def _runner() -> None:
        try:
            output["value"] = asyncio.run(value)
        except BaseException as exc:  # pragma: no cover
            error["value"] = exc

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()
    if "value" in error:
        raise error["value"]
    return output.get("value")


def _query_knowledge(args: Mapping[str, Any]) -> dict[str, Any]:
    """Query GRID's knowledge base (RAG system) using tools bridge."""
    if not _BRIDGE_AVAILABLE:
        return {
            "skill": "rag.query_knowledge",
            "status": "error",
            "error": "Tools bridge not available",
        }

    bridge = get_tools_bridge()
    if not bridge.is_rag_available():
        return {
            "skill": "rag.query_knowledge",
            "status": "error",
            "error": "RAG module not available",
        }

    query = args.get("query")
    if not query:
        return {
            "skill": "rag.query_knowledge",
            "status": "error",
            "error": "Missing required parameter: 'query'",
        }

    top_k = int(args.get("top_k", 5) or 5)
    temperature = float(args.get("temperature", 0.7) or 0.7)

    try:
        # Get RAG engine through bridge
        engine = bridge.get_rag_engine()
        if engine is None:
            return {
                "skill": "rag.query_knowledge",
                "status": "error",
                "error": "Failed to initialize RAG engine",
                "query": query,
            }
        result = engine.query(
            query_text=query,
            top_k=top_k,
            temperature=temperature,
            include_sources=True,
        )
        result = _resolve_awaitable(result)

        # Normalize output
        sources = []
        if result.get("sources"):
            sources.extend(
                {
                    "path": source.get("metadata", {}).get("path", "unknown"),
                    "distance": source.get("distance", 0),
                    "confidence": 1.0 - (source.get("distance", 0) / 2.0),  # Convert distance to confidence
                }
                for source in result["sources"]
            )

        return {
            "skill": "rag.query_knowledge",
            "status": "success",
            "query": query,
            "answer": result.get("answer", ""),
            "sources": sources,
            "retrieval_count": len(sources),
            "context_quality": sum(s["confidence"] for s in sources) / len(sources) if sources else 0,
        }

    except Exception as e:
        return {
            "skill": "rag.query_knowledge",
            "status": "error",
            "error": str(e),
            "query": query,
        }


# Register skill
rag_query_knowledge = SimpleSkill(
    id="rag.query_knowledge",
    name="RAG Knowledge Query",
    description="Query GRID's project knowledge base for documentation and context",
    handler=_query_knowledge,
)
