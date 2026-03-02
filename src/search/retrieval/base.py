"""Base retriever interface following the GRID-main ABC contract pattern.

Mirrors the dual sync/async convention used by BaseVectorStore,
BaseEmbeddingProvider, and BaseReranker in tools.rag.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import ScoredCandidate


class BaseRetriever(ABC):
    """Abstract base for all search retrievers."""

    @abstractmethod
    def retrieve(
        self,
        query_text: str,
        n_results: int = 100,
        allowed_ids: set[str] | None = None,
    ) -> list[ScoredCandidate]:
        """Retrieve scored candidates matching the query."""
        pass

    async def async_retrieve(
        self,
        query_text: str,
        n_results: int = 100,
        allowed_ids: set[str] | None = None,
    ) -> list[ScoredCandidate]:
        """Async variant. Default delegates to the sync implementation."""
        return self.retrieve(query_text, n_results, allowed_ids)
