"""Hybrid fusion: merges structured, semantic, and keyword results using RRF."""

from __future__ import annotations

import logging
from collections import defaultdict

from ..models import QueryIntent, ScoredCandidate, SearchQuery
from .keyword import KeywordRetriever
from .semantic import SemanticRetriever
from .structured import StructuredRetriever

logger = logging.getLogger(__name__)

INTENT_WEIGHTS: dict[QueryIntent, tuple[float, float]] = {
    QueryIntent.NAVIGATIONAL: (0.7, 0.3),
    QueryIntent.EXPLORATORY: (0.4, 0.6),
    QueryIntent.ANALYTICAL: (0.6, 0.4),
}


class HybridFusion:
    """Combines three retrieval signals via Reciprocal Rank Fusion.

    When structured filters are present the fusion first restricts the
    candidate set to the structured result, then applies weighted RRF
    across keyword and semantic scores.  The intent adjusts the keyword
    vs. semantic weight ratio.
    """

    def __init__(
        self,
        structured_retriever: StructuredRetriever,
        semantic_retriever: SemanticRetriever,
        keyword_retriever: KeywordRetriever,
        rrf_k: int = 60,
    ) -> None:
        self.structured = structured_retriever
        self.semantic = semantic_retriever
        self.keyword = keyword_retriever
        self.rrf_k = rrf_k

    def fuse(self, query: SearchQuery, n_results: int = 100) -> list[ScoredCandidate]:
        """Execute all retrievers and fuse their results."""
        allowed_ids: set[str] | None = None
        if query.filters:
            struct_results = self.structured.retrieve(query.filters)
            if not struct_results:
                return []
            allowed_ids = {c.doc_id for c in struct_results}

        search_text = query.text
        if query.expanded_terms:
            search_text = f"{search_text} {' '.join(query.expanded_terms)}"

        sem_results = self.semantic.retrieve(search_text, n_results=n_results, allowed_ids=allowed_ids)
        kw_results = self.keyword.retrieve(search_text, n_results=n_results, allowed_ids=allowed_ids)

        kw_weight, sem_weight = INTENT_WEIGHTS.get(query.intent, (0.5, 0.5))

        return self._rrf_merge(kw_results, sem_results, kw_weight, sem_weight, n_results)

    def _rrf_merge(
        self,
        kw_results: list[ScoredCandidate],
        sem_results: list[ScoredCandidate],
        kw_weight: float,
        sem_weight: float,
        n_results: int,
    ) -> list[ScoredCandidate]:
        k = self.rrf_k
        rrf_scores: dict[str, float] = defaultdict(float)

        for rank, c in enumerate(kw_results):
            rrf_scores[c.doc_id] += kw_weight / (k + rank + 1)

        for rank, c in enumerate(sem_results):
            rrf_scores[c.doc_id] += sem_weight / (k + rank + 1)

        sorted_ids = sorted(rrf_scores, key=rrf_scores.__getitem__, reverse=True)[:n_results]

        return [ScoredCandidate(doc_id=doc_id, score=rrf_scores[doc_id], source="fusion") for doc_id in sorted_ids]
