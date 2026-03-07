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
        self._doc_texts: list[str] = []

    def update(self, bm25_instance: Any, doc_ids: list[str], doc_texts: list[str] | None = None) -> None:
        """Refresh internal pointers after the index changes."""
        self._bm25 = bm25_instance
        self._doc_ids = list(doc_ids)
        self._doc_texts = list(doc_texts) if doc_texts else []

    def retrieve(
        self,
        query_text: str,
        n_results: int = 100,
        allowed_ids: set[str] | None = None,
    ) -> list[ScoredCandidate]:
        if self._bm25 is None or not query_text.strip():
            # Fallback: simple term matching when BM25 not available
            return self._fallback_retrieve(query_text, n_results, allowed_ids)

        tokens = TOKEN_PATTERN.findall(query_text.lower())
        if not tokens:
            return []

        scores = self._bm25.get_scores(tokens)
        indexed = [(self._doc_ids[i], float(scores[i])) for i in range(len(scores))]
        indexed.sort(key=lambda x: x[1], reverse=True)

        candidates: list[ScoredCandidate] = []
        for doc_id, score in indexed:
            if score < 0:
                break
            if allowed_ids is not None and doc_id not in allowed_ids:
                continue
            candidates.append(ScoredCandidate(doc_id=doc_id, score=score, source="keyword"))
            if len(candidates) >= n_results:
                break

        return candidates

    def _fallback_retrieve(
        self,
        query_text: str,
        n_results: int,
        allowed_ids: set[str] | None,
    ) -> list[ScoredCandidate]:
        """Simple fallback keyword search using substring matching."""
        if not query_text.strip() or not self._doc_ids:
            return []

        query_lower = query_text.lower()
        candidates: list[ScoredCandidate] = []

        for i, doc_id in enumerate(self._doc_ids):
            if allowed_ids is not None and doc_id not in allowed_ids:
                continue

            # Get the original document text (assuming it's stored)
            # For fallback, we'll use a simple scoring based on term matches
            doc_texts = getattr(self, "_doc_texts", [])
            doc_text = doc_texts[i] if i < len(doc_texts) else None
            if doc_text is None:
                continue

            doc_lower = doc_text.lower()

            # Simple scoring: count occurrences of query terms
            score = 0
            query_terms = set(TOKEN_PATTERN.findall(query_lower))
            doc_terms = set(TOKEN_PATTERN.findall(doc_lower))

            # Exact term matches get higher score
            exact_matches = query_terms & doc_terms
            score += len(exact_matches) * 2

            # Substring matches get lower score
            for term in query_terms:
                if term in doc_lower:
                    score += 0.5

            if score > 0:
                candidates.append(ScoredCandidate(doc_id=doc_id, score=score, source="keyword"))

        # Sort by score descending and limit results
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:n_results]
