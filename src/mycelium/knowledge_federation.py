"""
Knowledge Federation — Federated query engine across GRID and Pathways.

Sends a single query to both GRID's RAG pipeline and Pathways' ScopedRAG,
merges the results, and runs pattern detection across the combined corpus.
Patterns that only emerge when both knowledge bases are consulted become visible.

Communication with Pathways is via the event bus (not direct import),
maintaining the decoupled architecture.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from mycelium.core import PersonaProfile, SynthesisResult
from mycelium.synthesizer import Synthesizer
from unified_fabric import Event, EventDomain, EventResponse, get_event_bus

logger = logging.getLogger(__name__)

# Default timeout for each backend query (seconds)
_BACKEND_TIMEOUT: float = 5.0


@runtime_checkable
class RAGBackend(Protocol):
    """Protocol for a RAG backend that can answer questions."""

    async def query(self, question: str, top_k: int = 5) -> list[str]:
        """Query the backend and return text chunks."""
        ...


@dataclass
class FederatedResult:
    """Result of a federated knowledge query."""

    question: str
    grid_results: list[str] = field(default_factory=list)
    pathways_results: list[str] = field(default_factory=list)
    synthesis: SynthesisResult | None = None
    sources: list[str] = field(default_factory=list)
    patterns_applied: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class GridRAGAdapter:
    """Wraps GRID's RAG engine as a RAGBackend.

    If no RAG engine is available, returns empty results gracefully.
    """

    def __init__(self, rag_engine: Any = None) -> None:
        self._engine = rag_engine

    async def query(self, question: str, top_k: int = 5) -> list[str]:
        """Query GRID's RAG pipeline."""
        if self._engine is None:
            logger.debug("No GRID RAG engine configured — returning empty results")
            return []

        try:
            # Adapt to whatever interface the RAG engine exposes
            if hasattr(self._engine, "query"):
                result = await self._engine.query(question, top_k=top_k)
                if isinstance(result, list):
                    return [str(r) for r in result]
                return [str(result)]
            return []
        except Exception as e:
            logger.error("GRID RAG query failed: %s", e)
            return []


class PathwaysRAGAdapter:
    """Wraps Pathways' ScopedRAG via the event bus (not direct import).

    Sends a knowledge query event and waits for the result event via
    the request-reply pattern.
    """

    def __init__(self, timeout: float = _BACKEND_TIMEOUT) -> None:
        self._event_bus = get_event_bus()
        self._timeout = timeout

    async def query(self, question: str, top_k: int = 5) -> list[str]:
        """Query Pathways' ScopedRAG via event bus."""
        event = Event(
            event_type="pathways.knowledge.query",
            payload={
                "question": question,
                "top_k": top_k,
            },
            source_domain=EventDomain.GRID.value,
            target_domains=[EventDomain.PATHWAYS.value],
        )

        try:
            response: EventResponse = await self._event_bus.request_reply(event, timeout=self._timeout)
            if response.success and isinstance(response.data, list):
                return [str(r) for r in response.data]
            if response.success and isinstance(response.data, dict):
                return [str(r) for r in response.data.get("results", [])]
            return []
        except Exception as e:
            logger.error("Pathways knowledge query failed: %s", e)
            return []


class KnowledgeFederator:
    """Federated knowledge query engine.

    Sends queries to both GRID and Pathways RAG backends concurrently,
    combines results, and runs synthesis with pattern detection across
    the merged corpus.
    """

    def __init__(
        self,
        grid_backend: RAGBackend | None = None,
        pathways_backend: RAGBackend | None = None,
        synthesizer: Synthesizer | None = None,
        persona: PersonaProfile | None = None,
    ) -> None:
        self._grid_backend = grid_backend or GridRAGAdapter()
        self._pathways_backend = pathways_backend or PathwaysRAGAdapter()
        self._synthesizer = synthesizer or Synthesizer(persona or PersonaProfile())

    async def query(
        self,
        question: str,
        top_k: int = 5,
        timeout: float = _BACKEND_TIMEOUT,  # noqa: ASYNC109
    ) -> FederatedResult:
        """Query both backends and synthesize combined results.

        Args:
            question: The question to answer
            top_k: Number of results per backend
            timeout: Timeout per backend in seconds

        Returns:
            FederatedResult with merged results and cross-corpus patterns
        """
        # Query both backends concurrently with timeout
        grid_task = asyncio.create_task(self._safe_query(self._grid_backend, question, top_k, timeout))
        pathways_task = asyncio.create_task(self._safe_query(self._pathways_backend, question, top_k, timeout))

        grid_results, pathways_results = await asyncio.gather(grid_task, pathways_task)

        # Determine sources
        sources: list[str] = []
        if grid_results:
            sources.append("grid")
        if pathways_results:
            sources.append("pathways")

        # Combine and synthesize
        combined_texts = [f"[GRID] {t}" for t in grid_results]
        combined_texts.extend(f"[Pathways] {t}" for t in pathways_results)

        synthesis: SynthesisResult | None = None
        patterns_applied: list[str] = []

        if combined_texts:
            synthesis = self._synthesizer.synthesize_multiple(combined_texts)
            patterns_applied = synthesis.patterns_applied if synthesis else []

        result = FederatedResult(
            question=question,
            grid_results=grid_results,
            pathways_results=pathways_results,
            synthesis=synthesis,
            sources=sources,
            patterns_applied=patterns_applied,
        )

        # Broadcast federated result event
        await self._broadcast_result(result)

        return result

    async def _safe_query(
        self,
        backend: RAGBackend,
        question: str,
        top_k: int,
        timeout: float,  # noqa: ASYNC109
    ) -> list[str]:
        """Query a backend with timeout and graceful degradation."""
        try:
            async with asyncio.timeout(timeout):
                return await backend.query(question, top_k=top_k)
        except TimeoutError:
            logger.warning("Backend query timed out after %.1fs", timeout)
            return []
        except Exception as e:
            logger.error("Backend query failed: %s", e)
            return []

    async def _broadcast_result(self, result: FederatedResult) -> None:
        """Broadcast the federated result on the event bus."""
        event_bus = get_event_bus()
        event = Event(
            event_type="grid.knowledge.federated",
            payload={
                "question": result.question,
                "sources": result.sources,
                "results": result.grid_results + result.pathways_results,
                "patterns_applied": result.patterns_applied,
            },
            source_domain=EventDomain.GRID.value,
            target_domains=["all"],
        )
        await event_bus.publish(event)
