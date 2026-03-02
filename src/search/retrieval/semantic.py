"""Semantic retriever: dense vector similarity search via BaseVectorStore."""

from __future__ import annotations

import logging
from typing import Any

from ..models import ScoredCandidate
from .base import BaseRetriever

logger = logging.getLogger(__name__)


class SemanticRetriever(BaseRetriever):
    """Embeds the query and retrieves documents by cosine similarity.

    Wraps any BaseVectorStore implementation (ChromaDB, in-memory FAISS, etc.).
    """

    def __init__(self, vector_store: Any, embedding_provider: Any) -> None:
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider

    def retrieve(
        self,
        query_text: str,
        n_results: int = 100,
        allowed_ids: set[str] | None = None,
    ) -> list[ScoredCandidate]:
        if not query_text.strip():
            return []

        query_emb = self.embedding_provider.embed(query_text)
        if hasattr(query_emb, "tolist"):
            query_emb = query_emb.tolist()

        results = self.vector_store.query(query_embedding=query_emb, n_results=n_results)

        ids = results.get("ids", [])
        distances = results.get("distances", [])

        candidates: list[ScoredCandidate] = []
        for i, doc_id in enumerate(ids):
            dist = distances[i] if i < len(distances) else 1.0
            score = 1.0 / (1.0 + dist)
            if allowed_ids is not None and doc_id not in allowed_ids:
                continue
            candidates.append(ScoredCandidate(doc_id=doc_id, score=score, source="semantic"))

        return candidates

    async def async_retrieve(
        self,
        query_text: str,
        n_results: int = 100,
        allowed_ids: set[str] | None = None,
    ) -> list[ScoredCandidate]:
        if not query_text.strip():
            return []

        query_emb = await self.embedding_provider.async_embed(query_text)
        if hasattr(query_emb, "tolist"):
            query_emb = query_emb.tolist()

        results = self.vector_store.query(query_embedding=query_emb, n_results=n_results)

        ids = results.get("ids", [])
        distances = results.get("distances", [])

        candidates: list[ScoredCandidate] = []
        for i, doc_id in enumerate(ids):
            dist = distances[i] if i < len(distances) else 1.0
            score = 1.0 / (1.0 + dist)
            if allowed_ids is not None and doc_id not in allowed_ids:
                continue
            candidates.append(ScoredCandidate(doc_id=doc_id, score=score, source="semantic"))

        return candidates
