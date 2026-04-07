"""
Optional LangChain integration for GRID RAG.

This module is imported behind a try/except block from ``tools.rag.__init__``.
If LangChain dependencies are missing, importing this module raises ImportError
so callers can gracefully degrade.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping

try:
    from langchain_core.runnables import RunnableLambda
    from langchain_core.tools import tool
except ImportError as exc:  # pragma: no cover - optional dependency gate
    raise ImportError("LangChain dependencies are not installed") from exc

from .engine import RAGEngine, create_conversational_engine

_GRAPH_DECISION_HINTS: dict[str, str] = {
    "SCHEMA_INVALID": "Validate node/edge schema and ensure required fields are present.",
    "GRAPH_TOO_LARGE": "Lower max_nodes/max_edges or apply filtering before rendering.",
    "LAYOUT_TIMEOUT": "Retry with reduced graph size or increase client timeout budget.",
    "INCONSISTENT_GRAPH": "Re-run ingestion to repair missing node references.",
    "UNSUPPORTED_REQUEST": "Adjust request parameters to supported bounds.",
}


def configure_langsmith(project_name: str = "grid-rag", enabled: bool = True) -> bool:
    """Configure basic LangSmith tracing env vars for this process."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if enabled else "false"
    os.environ["LANGCHAIN_PROJECT"] = project_name
    return enabled


def is_tracing_enabled() -> bool:
    """Return whether LangSmith tracing is enabled in process env."""
    return os.environ.get("LANGCHAIN_TRACING_V2", "").lower() in {"1", "true", "yes"}


@dataclass(slots=True)
class ConversationalRAGAgent:
    """Lightweight agent wrapper exposing async RAG query and diagnostics helpers."""

    engine: RAGEngine
    top_k: int = 8
    temperature: float = 0.3

    async def ask(self, query: str) -> dict[str, Any]:
        return await self.engine.query(
            query_text=query,
            top_k=self.top_k,
            temperature=self.temperature,
            include_sources=True,
        )

    async def explain_graph_decision(self, decision: Mapping[str, Any]) -> dict[str, Any]:
        code = str(decision.get("code", "UNSUPPORTED_REQUEST"))
        hint = _GRAPH_DECISION_HINTS.get(
            code,
            "Inspect graph limits and retry with narrower scope.",
        )
        prompt = (
            "You are troubleshooting a graph rendering failure.\n"
            f"Decision code: {code}\n"
            f"Decision payload: {dict(decision)}\n"
            f"Baseline remediation hint: {hint}\n"
            "Provide 3 concrete mitigation steps."
        )
        return await self.ask(prompt)


def create_rag_agent(
    *,
    engine: RAGEngine | None = None,
    top_k: int = 8,
    temperature: float = 0.3,
) -> ConversationalRAGAgent:
    """Create a conversational RAG agent with optional existing engine."""
    return ConversationalRAGAgent(
        engine=engine or create_conversational_engine(),
        top_k=top_k,
        temperature=temperature,
    )


def create_conversational_agent(
    *,
    engine: RAGEngine | None = None,
    top_k: int = 8,
    temperature: float = 0.3,
) -> ConversationalRAGAgent:
    """Alias for create_rag_agent for backward compatibility."""
    return create_rag_agent(engine=engine, top_k=top_k, temperature=temperature)


def create_simple_rag_chain(
    *,
    engine: RAGEngine | None = None,
    top_k: int = 8,
    temperature: float = 0.3,
) -> RunnableLambda:
    """
    Create a simple async LangChain runnable around GRID RAG query.

    Input can be a raw string or an object containing ``query``.
    """
    rag_engine = engine or create_conversational_engine()

    async def _query(input_data: str | Mapping[str, Any]) -> dict[str, Any]:
        if isinstance(input_data, str):
            query_text = input_data
        else:
            query_text = str(input_data.get("query", ""))
        return await rag_engine.query(
            query_text=query_text,
            top_k=top_k,
            temperature=temperature,
            include_sources=True,
        )

    return RunnableLambda(
        lambda _input: {"error": "Use `ainvoke` for async execution of GRID RAG chain."},
        afunc=_query,
    )


def create_rag_tool(
    *,
    engine: RAGEngine | None = None,
    top_k: int = 8,
    temperature: float = 0.3,
):
    """Expose GRID RAG query as a LangChain tool."""
    rag_engine = engine or create_conversational_engine()

    @tool("grid_rag_query")
    async def rag_query(query: str) -> str:
        """Query GRID RAG and return answer text."""
        result = await rag_engine.query(
            query_text=query,
            top_k=top_k,
            temperature=temperature,
            include_sources=True,
        )
        return str(result.get("answer", ""))

    return rag_query
