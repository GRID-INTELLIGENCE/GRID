"""Cross-encoder reranking adapter for the search engine.

Wraps the existing CrossEncoderReranker from the RAG module as the
final precision-focused reranking stage.
"""

from __future__ import annotations

import logging
from typing import Any

from ..models import ScoredCandidate

logger = logging.getLogger(__name__)

try:
    from tools.rag.retrieval.cross_encoder_reranker import CrossEncoderReranker

    HAS_CROSS_ENCODER = True
except ImportError:
    HAS_CROSS_ENCODER = False
    CrossEncoderReranker = None  # type: ignore


class SearchCrossEncoder:
    """Applies cross-encoder reranking to the top-K candidates.

    Uses the sentence-transformers CrossEncoder (ms-marco-MiniLM-L6-v2 by
    default) which scores each (query, document_text) pair jointly for
    higher precision than bi-encoder similarity.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L6-v2",
        top_k: int = 20,
    ) -> None:
        self.top_k = top_k
        self._reranker: Any = None
        self.model_name = model_name
        self.enabled = False

        if HAS_CROSS_ENCODER:
            try:
                self._reranker = CrossEncoderReranker(
                    model_name=model_name,
                    max_candidates=top_k,
                )
                self.enabled = True
            except Exception:
                logger.warning("Cross-encoder model failed to load; reranking disabled")

    def rerank(
        self,
        query_text: str,
        candidates: list[ScoredCandidate],
        doc_texts: dict[str, str],
    ) -> list[ScoredCandidate]:
        """Rerank the top-K candidates using the cross-encoder."""
        if not self.enabled or self._reranker is None:
            return candidates

        top_candidates = candidates[: self.top_k]
        remaining = candidates[self.top_k :]

        texts = [doc_texts.get(c.doc_id, "") for c in top_candidates]
        if not any(texts):
            return candidates

        ranked_pairs = self._reranker.rerank(query_text, texts, top_k=len(top_candidates))

        reranked: list[ScoredCandidate] = []
        for original_idx, ce_score in ranked_pairs:
            c = top_candidates[original_idx]
            reranked.append(
                ScoredCandidate(
                    doc_id=c.doc_id,
                    score=ce_score,
                    source="cross_encoder",
                )
            )

        reranked.extend(remaining)
        return reranked
