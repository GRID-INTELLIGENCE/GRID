"""Intent classifier for search queries.

Composes with the existing tools.rag.intelligence.IntentClassifier when
available, falling back to a lightweight rule-based + embedding heuristic
otherwise.  This avoids duplicating the RAG intelligence stack while
remaining usable when the full transformers pipeline is not loaded.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any

from ..models import QueryIntent, SearchQuery

logger = logging.getLogger(__name__)

try:
    from tools.rag.intelligence.intent_classifier import (
        IntentClassifier as RAGIntentClassifier,
    )

    HAS_RAG_INTENT = True
except ImportError:
    HAS_RAG_INTENT = False


@dataclass
class IntentResult:
    """Result of search intent classification (mirrors RAG IntentResult style)."""

    intent: QueryIntent
    confidence: float
    all_scores: dict[str, float]


class SearchIntentClassifier:
    """Classifies query intent to adjust retrieval weights dynamically.

    Three search-specific intents:
      - NAVIGATIONAL: query closely matches a known field value (boost exact match)
      - ANALYTICAL:   numeric filters dominate (prioritise structured filtering)
      - EXPLORATORY:  broad free-text (emphasise semantic diversity)

    When the RAG IntentClassifier is available it is consulted first; its
    richer intent taxonomy is mapped to the three search intents.
    """

    RAG_INTENT_MAP: dict[str, QueryIntent] = {
        "location": QueryIntent.NAVIGATIONAL,
        "definition": QueryIntent.NAVIGATIONAL,
        "comparison": QueryIntent.ANALYTICAL,
        "debugging": QueryIntent.ANALYTICAL,
        "implementation": QueryIntent.EXPLORATORY,
        "usage": QueryIntent.EXPLORATORY,
        "architecture": QueryIntent.EXPLORATORY,
        "relationship": QueryIntent.EXPLORATORY,
        "other": QueryIntent.EXPLORATORY,
    }

    def __init__(
        self,
        embedding_provider: Any | None = None,
        similarity_threshold: float = 0.85,
        analytical_threshold: float = 0.5,
        use_rag_classifier: bool = True,
    ) -> None:
        self.embedding_provider = embedding_provider
        self.similarity_threshold = similarity_threshold
        self.analytical_threshold = analytical_threshold
        self._field_value_embeddings: dict[str, list[tuple[str, Any]]] = {}

        self._rag_classifier: Any = None
        if use_rag_classifier and HAS_RAG_INTENT:
            try:
                self._rag_classifier = RAGIntentClassifier()
                logger.info("Composing with RAG IntentClassifier")
            except Exception:
                logger.debug("RAG IntentClassifier unavailable, using rule-based fallback")

    def register_field_values(self, field_name: str, values: list[str]) -> None:
        """Pre-compute embeddings for known field values to enable navigational detection."""
        if self.embedding_provider is None:
            return
        pairs: list[tuple[str, Any]] = []
        for v in values:
            emb = self.embedding_provider.embed(v)
            if hasattr(emb, "tolist"):
                emb = emb.tolist()
            pairs.append((v, emb))
        self._field_value_embeddings[field_name] = pairs

    def classify(self, query: SearchQuery) -> IntentResult:
        """Return an IntentResult for a parsed query."""

        if self._rag_classifier is not None and query.text.strip():
            try:
                rag_result = self._rag_classifier.classify(query.text)
                mapped = self.RAG_INTENT_MAP.get(rag_result.intent.value, QueryIntent.EXPLORATORY)
                return IntentResult(
                    intent=mapped,
                    confidence=rag_result.confidence,
                    all_scores=dict(rag_result.all_scores.items()),
                )
            except Exception:
                logger.debug("RAG classifier failed, falling back to rules")

        return self._rule_based(query)

    def _rule_based(self, query: SearchQuery) -> IntentResult:
        numeric_filter_count = sum(1 for f in query.filters if f.op in ("gt", "gte", "lt", "lte"))
        total_filters = len(query.filters)
        has_text = bool(query.text.strip())
        scores: dict[str, float] = {}

        if total_filters > 0 and numeric_filter_count / max(total_filters, 1) > self.analytical_threshold:
            confidence = min(1.0, 0.6 + 0.1 * numeric_filter_count)
            scores = {"analytical": confidence, "navigational": 0.0, "exploratory": 1.0 - confidence}
            return IntentResult(intent=QueryIntent.ANALYTICAL, confidence=confidence, all_scores=scores)

        if has_text and self.embedding_provider and self._field_value_embeddings:
            sim = self._best_field_similarity(query.text)
            if sim >= self.similarity_threshold:
                scores = {"navigational": sim, "analytical": 0.0, "exploratory": 1.0 - sim}
                return IntentResult(intent=QueryIntent.NAVIGATIONAL, confidence=sim, all_scores=scores)

        confidence = 0.7 if (has_text and total_filters == 0) else 0.5
        scores = {"exploratory": confidence, "navigational": 0.0, "analytical": 0.0}
        return IntentResult(intent=QueryIntent.EXPLORATORY, confidence=confidence, all_scores=scores)

    def _best_field_similarity(self, text: str) -> float:
        if self.embedding_provider is None:
            return 0.0
        query_emb = self._to_vector(self.embedding_provider.embed(text))
        norm_q = self._vector_norm(query_emb)
        if norm_q == 0:
            return 0.0
        query_emb = [value / norm_q for value in query_emb]

        best = 0.0
        for pairs in self._field_value_embeddings.values():
            for _, field_emb in pairs:
                vec = self._to_vector(field_emb)
                norm_v = self._vector_norm(vec)
                if norm_v == 0:
                    continue
                sim = self._dot_product(query_emb, [value / norm_v for value in vec])
                if sim > best:
                    best = sim
        return best

    @staticmethod
    def _to_vector(values: Any) -> list[float]:
        return [float(value) for value in values]

    @staticmethod
    def _vector_norm(values: list[float]) -> float:
        return math.sqrt(sum(value * value for value in values))

    @staticmethod
    def _dot_product(left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right))
