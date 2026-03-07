"""Query expansion via embedding nearest-neighbours in the corpus vocabulary."""

from __future__ import annotations

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)


class QueryExpander:
    """Expands a query with synonymous terms from the indexed vocabulary.

    Uses cosine similarity between the query term embeddings and a pre-built
    vocabulary embedding matrix to find related terms without an external API.
    """

    def __init__(
        self,
        embedding_provider: Any,
        similarity_threshold: float = 0.75,
        max_expansions: int = 3,
    ) -> None:
        self.embedding_provider = embedding_provider
        self.similarity_threshold = similarity_threshold
        self.max_expansions = max_expansions

        self._vocab: list[str] = []
        self._vocab_matrix: list[list[float]] = []

    def build_vocabulary(self, terms: list[str]) -> None:
        """Build the vocabulary embedding matrix from a list of corpus terms."""
        unique = sorted({t.lower().strip() for t in terms if t.strip()})
        if not unique:
            self._vocab = []
            self._vocab_matrix = []
            return

        embeddings = self.embedding_provider.embed_batch(unique)
        self._vocab_matrix = [self._normalize_vector(self._to_vector(embedding)) for embedding in embeddings]
        self._vocab = unique

    def expand(self, query_text: str) -> list[str]:
        """Return expansion terms for the given query text."""
        if not self._vocab_matrix or not query_text.strip():
            return []

        query_emb = self.embedding_provider.embed(query_text)
        q_vec = self._normalize_vector(self._to_vector(query_emb))
        if not q_vec:
            return []

        similarities = [self._dot_product(candidate, q_vec) for candidate in self._vocab_matrix]
        query_tokens = set(query_text.lower().split())

        candidates: list[tuple[str, float]] = []
        for idx in sorted(range(len(similarities)), key=similarities.__getitem__, reverse=True):
            term = self._vocab[idx]
            sim = float(similarities[idx])
            if sim < self.similarity_threshold:
                break
            if term in query_tokens:
                continue
            candidates.append((term, sim))
            if len(candidates) >= self.max_expansions:
                break

        return [term for term, _ in candidates]

    @staticmethod
    def _to_vector(values: Any) -> list[float]:
        return [float(value) for value in values]

    @staticmethod
    def _normalize_vector(values: list[float]) -> list[float]:
        norm = math.sqrt(sum(value * value for value in values))
        if norm == 0:
            return []
        return [value / norm for value in values]

    @staticmethod
    def _dot_product(left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right, strict=False))
