"""Query expansion via embedding nearest-neighbours in the corpus vocabulary."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

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
        self._vocab_matrix: np.ndarray | None = None

    def build_vocabulary(self, terms: list[str]) -> None:
        """Build the vocabulary embedding matrix from a list of corpus terms."""
        unique = sorted({t.lower().strip() for t in terms if t.strip()})
        if not unique:
            return

        embeddings = self.embedding_provider.embed_batch(unique)
        matrix = np.array(
            [e.tolist() if hasattr(e, "tolist") else list(e) for e in embeddings],
            dtype=np.float32,
        )

        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        self._vocab_matrix = matrix / norms
        self._vocab = unique

    def expand(self, query_text: str) -> list[str]:
        """Return expansion terms for the given query text."""
        if self._vocab_matrix is None or not query_text.strip():
            return []

        query_emb = self.embedding_provider.embed(query_text)
        q_vec = np.array(
            query_emb.tolist() if hasattr(query_emb, "tolist") else list(query_emb),
            dtype=np.float32,
        )
        norm = np.linalg.norm(q_vec)
        if norm == 0:
            return []
        q_vec = q_vec / norm

        similarities = self._vocab_matrix @ q_vec
        query_tokens = set(query_text.lower().split())

        candidates: list[tuple[str, float]] = []
        for idx in np.argsort(similarities)[::-1]:
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
