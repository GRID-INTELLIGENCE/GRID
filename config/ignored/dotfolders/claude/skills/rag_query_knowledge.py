"""
Skill: rag.query_knowledge

Query GRID's project knowledge base using the RAG system.
Retrieves relevant documentation and provides LLM-generated answers.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# Add grid root to path
grid_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(grid_root))

from grid.skills.base import SimpleSkill
from tools.rag.config import RAGConfig

# Import after path is set
from tools.rag.rag_engine import RAGEngine


def _query_knowledge(args: Mapping[str, Any]) -> dict[str, Any]:
    """Query GRID's knowledge base (RAG system)."""
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
        config = RAGConfig.from_env()
        config.ensure_local_only()

        engine = RAGEngine(config=config)
        result = engine.query(
            query_text=query,
            top_k=top_k,
            temperature=temperature,
            include_sources=True,
        )

        # Normalize output
        sources = []
        if result.get("sources"):
            for source in result["sources"]:
                sources.append(
                    {
                        "path": source.get("metadata", {}).get("path", "unknown"),
                        "distance": source.get("distance", 0),
                        "confidence": 1.0 - (source.get("distance", 0) / 2.0),  # Convert distance to confidence
                    }
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
