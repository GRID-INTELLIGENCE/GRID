from __future__ import annotations

import math
from typing import Any

from .base import BaseVectorStore

try:
    import faiss
    import numpy as np

    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False


class InMemoryDenseVectorStore(BaseVectorStore):
    def __init__(self, embedding_dim: int | None = None) -> None:
        self._ids: list[str] = []
        self._documents: list[str] = []
        self._embeddings: list[list[float]] = []
        self._metadatas: list[dict[str, Any]] = []
        self._index = None
        self._dirty = False
        self.embedding_dim = embedding_dim

    def add(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        if not (len(ids) == len(documents) == len(embeddings)):
            raise ValueError("ids, documents, and embeddings must have same length")

        if metadatas is None:
            metadatas = [{}] * len(documents)
        elif len(metadatas) != len(documents):
            raise ValueError("metadatas must have same length as documents")

        self._ids.extend(ids)
        self._documents.extend(documents)
        self._embeddings.extend(embeddings)
        self._metadatas.extend(metadatas)
        self._dirty = True

    def _rebuild_index(self) -> None:
        """Rebuild FAISS index from stored embeddings."""
        if not HAS_FAISS or not self._embeddings:
            self._index = None
            self._dirty = False
            return

        dim = len(self._embeddings[0])
        # Using IndexFlatIP with normalized vectors for cosine similarity
        self._index = faiss.IndexFlatIP(dim)
        data = np.array(self._embeddings).astype("float32")
        faiss.normalize_L2(data)
        self._index.add(data)
        self._dirty = False

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        if include is None:
            include = ["documents", "metadatas", "distances"]

        if not self._embeddings:
            return {"ids": [], "documents": [], "metadatas": [], "distances": []}

        # If there's a filter, we might prefer brute force or filtering FAISS results
        # For simplicity, use FAISS if no filter and available, else fallback
        if HAS_FAISS and where is None:
            if self._dirty or self._index is None:
                self._rebuild_index()

            if self._index:
                query_vec = np.array([query_embedding]).astype("float32")
                faiss.normalize_L2(query_vec)

                # Search FAISS
                # Fetching slightly more to ensure we have enough even with duplicates (idempotency)
                k = min(n_results, self._index.ntotal)
                distances, indices = self._index.search(query_vec, k)

                # FAISS IndexFlatIP returns similarity, we want distance = 1 - similarity
                final_ids = []
                final_docs = []
                final_metas = []
                final_dists = []

                for dist, idx in zip(distances[0], indices[0], strict=False):
                    if idx < 0:
                        continue
                    final_ids.append(self._ids[idx])
                    if "documents" in include:
                        final_docs.append(self._documents[idx])
                    if "metadatas" in include:
                        final_metas.append(self._metadatas[idx])
                    final_dists.append(float(1.0 - dist))

                return {
                    "ids": final_ids,
                    "documents": final_docs,
                    "metadatas": final_metas,
                    "distances": final_dists,
                }

        # Fallback to vectorized numpy or original loop
        if where is None:
            candidate_indices = list(range(len(self._documents)))
        else:
            candidate_indices = [
                i for i, meta in enumerate(self._metadatas) if all(meta.get(k) == v for k, v in where.items())
            ]

        if not candidate_indices:
            return {"ids": [], "documents": [], "metadatas": [], "distances": []}

        # Optimized brute force with numpy
        if HAS_FAISS:  # We have numpy if we have faiss
            embeddings = np.array([self._embeddings[i] for i in candidate_indices]).astype("float32")
            query = np.array(query_embedding).astype("float32")

            # Normalize for cosine distance
            faiss.normalize_L2(embeddings)
            query_norm = np.linalg.norm(query)
            if query_norm > 0:
                query = query / query_norm

            similarities = np.dot(embeddings, query)
            dists = 1.0 - similarities

            # Sort and pick top K
            scored = sorted(zip(candidate_indices, dists, strict=False), key=lambda x: x[1])
        else:
            # Original slow loop fallback
            scored = []
            for i in candidate_indices:
                dist = self._cosine_distance(query_embedding, self._embeddings[i])
                scored.append((i, dist))
            scored.sort(key=lambda x: x[1])

        scored = scored[: max(0, min(n_results, len(scored)))]

        ids = [self._ids[i] for i, _ in scored]
        documents = [self._documents[i] for i, _ in scored]
        metadatas = [self._metadatas[i] for i, _ in scored]
        distances = [d for _, d in scored]

        return {
            "ids": ids,
            "documents": documents if "documents" in include else [],
            "metadatas": metadatas if "metadatas" in include else [],
            "distances": distances if "distances" in include else [],
        }

    def delete(self, ids: list[str] | None = None, where: dict[str, Any] | None = None) -> None:
        if ids is None and where is None:
            raise ValueError("Must provide either ids or where filter")

        keep: list[int] = []
        for i, doc_id in enumerate(self._ids):
            if ids is not None and doc_id in ids:
                continue
            if where is not None and all(self._metadatas[i].get(k) == v for k, v in where.items()):
                continue
            keep.append(i)

        self._ids = [self._ids[i] for i in keep]
        self._documents = [self._documents[i] for i in keep]
        self._embeddings = [self._embeddings[i] for i in keep]
        self._metadatas = [self._metadatas[i] for i in keep]
        self._dirty = True

    def count(self) -> int:
        return len(self._documents)

    @staticmethod
    def _cosine_distance(a: list[float], b: list[float]) -> float:
        if len(a) == 0 or len(b) == 0:
            return 1.0
        n = min(len(a), len(b))
        dot = 0.0
        na = 0.0
        nb = 0.0
        for i in range(n):
            av = float(a[i])
            bv = float(b[i])
            dot += av * bv
            na += av * av
            nb += bv * bv
        if na == 0.0 or nb == 0.0:
            return 1.0
        sim = dot / (math.sqrt(na) * math.sqrt(nb))
        return 1.0 - sim


# Backward compatibility alias
InMemoryDenseStore = InMemoryDenseVectorStore
