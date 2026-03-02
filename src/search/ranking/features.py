"""Feature extraction for learning-to-rank: builds a feature vector per query-document pair."""

from __future__ import annotations

import re
from datetime import UTC, datetime

import numpy as np

from ..models import Document, FieldType, IndexSchema, ScoredCandidate

TOKEN_PATTERN = re.compile(r"\b\w+\b")

FEATURE_NAMES: list[str] = [
    "bm25_score",
    "vector_similarity",
    "rrf_rank",
    "field_match_count",
    "query_doc_len_ratio",
    "field_weight_sum",
    "freshness",
    "popularity",
]


class FeatureExtractor:
    """Extracts an 8-dimensional feature vector for each query-document pair.

    Features combine signals from multiple retrieval stages (BM25, vector,
    fusion rank) with structural cues from the schema (field weights,
    freshness, popularity).
    """

    def __init__(
        self,
        schema: IndexSchema,
        freshness_decay_hours: float = 24.0,
        popularity_fields: list[str] | None = None,
    ) -> None:
        self.schema = schema
        self.freshness_decay_hours = freshness_decay_hours
        self.popularity_fields = popularity_fields or ["popularity", "click_count", "impressions", "views"]

    def extract(
        self,
        query_text: str,
        doc: Document,
        candidate: ScoredCandidate,
        bm25_scores: dict[str, float],
        vector_scores: dict[str, float],
        rrf_rank: int,
    ) -> np.ndarray:
        bm25 = bm25_scores.get(doc.id, 0.0)
        vector_sim = vector_scores.get(doc.id, 0.0)

        query_tokens = set(TOKEN_PATTERN.findall(query_text.lower()))
        field_match_count = 0
        field_weight_sum = 0.0
        doc_text_len = 0

        for field_name, field_schema in self.schema.fields.items():
            value = doc.fields.get(field_name)
            if value is None:
                continue
            field_str = str(value).lower()
            doc_text_len += len(field_str)
            matched = query_tokens & set(TOKEN_PATTERN.findall(field_str))
            if matched:
                field_match_count += len(matched)
                field_weight_sum += field_schema.weight * len(matched)

        query_len = max(len(query_text), 1)
        doc_len = max(doc_text_len, 1)
        query_doc_len_ratio = query_len / doc_len

        freshness = self._compute_freshness(doc)
        popularity = self._compute_popularity(doc)

        return np.array(
            [
                bm25,
                vector_sim,
                float(rrf_rank),
                float(field_match_count),
                query_doc_len_ratio,
                field_weight_sum,
                freshness,
                popularity,
            ],
            dtype=np.float32,
        )

    def extract_batch(
        self,
        query_text: str,
        docs: list[Document],
        candidates: list[ScoredCandidate],
        bm25_scores: dict[str, float],
        vector_scores: dict[str, float],
    ) -> np.ndarray:
        """Extract features for a batch of candidates. Returns (n, 8) matrix."""
        features = [
            self.extract(query_text, doc, cand, bm25_scores, vector_scores, rank)
            for rank, (doc, cand) in enumerate(zip(docs, candidates, strict=False))
        ]
        return np.vstack(features) if features else np.empty((0, len(FEATURE_NAMES)), dtype=np.float32)

    def _compute_freshness(self, doc: Document) -> float:
        """Normalised freshness: 1.0 for brand-new, decays towards 0.0."""
        for field_name, field_schema in self.schema.fields.items():
            if field_schema.type != FieldType.DATETIME:
                continue
            raw = doc.fields.get(field_name)
            if raw is None:
                continue
            try:
                dt = raw if isinstance(raw, datetime) else datetime.fromisoformat(str(raw))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                age_hours = (datetime.now(UTC) - dt).total_seconds() / 3600
                return 1.0 / (1.0 + age_hours / self.freshness_decay_hours)
            except (ValueError, TypeError):
                continue
        return 0.5

    def _compute_popularity(self, doc: Document) -> float:
        for name in self.popularity_fields:
            val = doc.fields.get(name)
            if val is not None:
                try:
                    return float(val)
                except (TypeError, ValueError):
                    continue
        return 0.0
