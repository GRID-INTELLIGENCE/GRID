"""Ranking pipeline orchestrator: features -> LTR -> cross-encoder -> final scores."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..config import SearchConfig
from ..models import Document, IndexSchema, ScoredCandidate, SearchQuery
from .cross_encoder import SearchCrossEncoder

try:
    from .features import FeatureExtractor
except ImportError:
    FeatureExtractor = None  # type: ignore[assignment]

try:
    from .ltr_model import LTRModel
except ImportError:
    LTRModel = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class RankingPipeline:
    """Orchestrates the full ranking stack:

    1. Extract feature vectors for all candidates
    2. Apply LTR model (if trained) or fall back to fusion scores
    3. Apply cross-encoder reranking to top-K for maximum precision
    """

    def __init__(self, schema: IndexSchema, config: SearchConfig | None = None) -> None:
        self.config = config or SearchConfig()
        self.feature_extractor = None
        if FeatureExtractor is not None:
            self.feature_extractor = FeatureExtractor(
                schema,
                freshness_decay_hours=self.config.freshness_decay_hours,
                popularity_fields=self.config.popularity_fields,
            )
        else:
            logger.warning("Feature extractor unavailable; learning-to-rank disabled")

        self._ltr: Any = None
        if self.config.ltr_model_path and LTRModel is not None:
            try:
                self._ltr = LTRModel()
                self._ltr.load(self.config.ltr_model_path)
            except Exception:
                logger.warning("Failed to load LTR model from %s", self.config.ltr_model_path)
                self._ltr = None
        elif self.config.ltr_model_path:
            logger.warning("LTR model path configured but scientific stack is unavailable; skipping LTR loading")

        self._cross_encoder: SearchCrossEncoder | None = None
        if self.config.cross_encoder_enabled:
            try:
                self._cross_encoder = SearchCrossEncoder(
                    model_name=self.config.cross_encoder_model,
                    top_k=self.config.cross_encoder_top_k,
                )
            except Exception:
                logger.warning("Cross-encoder init failed; disabled")

    def rank(
        self,
        query: SearchQuery,
        candidates: list[ScoredCandidate],
        documents: dict[str, Document],
        doc_texts: dict[str, str],
        bm25_scores: dict[str, float],
        vector_scores: dict[str, float],
    ) -> list[ScoredCandidate]:
        if not candidates:
            return []

        docs = [documents[c.doc_id] for c in candidates if c.doc_id in documents]
        valid_candidates = [c for c in candidates if c.doc_id in documents]

        if not valid_candidates:
            return candidates

        if self._ltr and self._ltr.is_fitted and self.feature_extractor is not None:
            feature_matrix = self.feature_extractor.extract_batch(
                query.text,
                docs,
                valid_candidates,
                bm25_scores,
                vector_scores,
            )
            ltr_scores = self._ltr.predict(feature_matrix)

            for i, c in enumerate(valid_candidates):
                valid_candidates[i] = ScoredCandidate(
                    doc_id=c.doc_id,
                    score=float(ltr_scores[i]),
                    source="ltr",
                )

            valid_candidates.sort(key=lambda c: c.score, reverse=True)

        if self._cross_encoder and self._cross_encoder.enabled:
            valid_candidates = self._cross_encoder.rerank(
                query.text,
                valid_candidates,
                doc_texts,
            )

        return valid_candidates

    def train_ltr(
        self,
        features: Any,
        labels: Any,
        save_path: str | None = None,
    ) -> dict[str, float]:
        """Train (or retrain) the LTR model on labelled data."""
        if LTRModel is None or self.feature_extractor is None:
            raise ImportError("Learning-to-rank requires NumPy/scikit-learn dependencies")
        self._ltr = LTRModel()
        metrics = self._ltr.train(features, labels)
        if save_path:
            self._ltr.save(Path(save_path))
        return metrics
