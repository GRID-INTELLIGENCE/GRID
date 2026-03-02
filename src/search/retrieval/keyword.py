"""Keyword retriever: BM25 sparse scoring over the indexed corpus."""

from __future__ import annotations

import logging
import re
from typing import Any

from ..models import ScoredCandidate
from .base import BaseRetriever

logger = logging.getLogger(__name__)
TOKEN_PATTERN = re.compile(r"\b\w+\b")


class KeywordRetriever(BaseRetriever):
    """BM25-based keyword retriever using rank_bm25.BM25Okapi.

    Tokenises the query and scores it against the pre-built BM25 corpus
    maintained by the IndexingPipeline.
    """

    def __init__(self) -> None:
        self._bm25: Any = None
        self._doc_ids: list[str] = []

    def update(self, bm25_instance: Any, doc_ids: list[str]) -> None:
        """Refresh internal pointers after the index changes."""
        self._bm25 = bm25_instance
        self._doc_ids = list(doc_ids)

    def retrieve(
        self,
        query_text: str,
        n_results: int = 100,
        allowed_ids: set[str] | None = None,
    ) -> list[ScoredCandidate]:
        if self._bm25 is None or not query_text.strip():
            return []

        tokens = TOKEN_PATTERN.findall(query_text.lower())
        if not tokens:
            return []

        scores = self._bm25.get_scores(tokens)
        indexed = [(self._doc_ids[i], float(scores[i])) for i in range(len(scores))]
        indexed.sort(key=lambda x: x[1], reverse=True)

        candidates: list[ScoredCandidate] = []
        for doc_id, score in indexed[:n_results]:
            if score <= 0:
                break
            if allowed_ids is not None and doc_id not in allowed_ids:
                continue
            candidates.append(ScoredCandidate(doc_id=doc_id, score=score, source="keyword"))

        return candidates
