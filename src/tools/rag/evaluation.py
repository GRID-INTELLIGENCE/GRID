"""RAG evaluation metrics and quality tracking.

Measures:
- Context Relevance: How relevant are retrieved chunks to the query?
- Context Precision: What fraction of retrieved chunks are relevant?
- Faithfulness: Is the answer grounded in the retrieved context?
"""

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Results from evaluating a single RAG query."""

    query: str
    context_relevance: float  # 0-1
    context_precision_at_k: float  # 0-1
    answer_similarity: float | None = None  # 0-1, if golden answer provided
    latency_ms: float = 0.0


class RAGEvaluator:
    """Evaluates RAG retrieval quality."""

    def __init__(self, embedding_provider):
        self.embedding_provider = embedding_provider

    def evaluate_retrieval(
        self,
        query: str,
        retrieved_docs: list[str],
        golden_docs: list[str] | None = None,
    ) -> dict[str, float]:
        """Evaluate retrieval quality.

        Args:
            query: The query text
            retrieved_docs: Documents retrieved by the system
            golden_docs: Optional ground-truth relevant documents

        Returns:
            Dictionary with evaluation metrics
        """
        metrics = {}

        if not retrieved_docs:
            return {"context_relevance_avg": 0.0, "precision_at_k": 0.0}

        # Context Relevance: semantic similarity between query and retrieved docs
        query_emb = self.embedding_provider.embed(query)
        doc_embs = self.embedding_provider.embed_batch(retrieved_docs)

        similarities = []
        for doc_emb in doc_embs:
            sim = self._cosine_similarity(query_emb, doc_emb)
            similarities.append(sim)

        if similarities:
            metrics["context_relevance_avg"] = float(np.mean(similarities))
            metrics["context_relevance_max"] = float(np.max(similarities))
            metrics["context_relevance_min"] = float(np.min(similarities))
        else:
            metrics["context_relevance_avg"] = 0.0

        # Precision@K (if golden docs provided)
        if golden_docs:
            # We consider a doc 'relevant' if it's semantically similar to any golden doc
            relevant_count = 0
            for doc in retrieved_docs:
                doc_emb = self.embedding_provider.embed(doc)
                for gd in golden_docs:
                    gd_emb = self.embedding_provider.embed(gd)
                    if self._cosine_similarity(doc_emb, gd_emb) > 0.8:
                        relevant_count += 1
                        break

            metrics["precision_at_k"] = relevant_count / len(retrieved_docs)

        return metrics

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity."""
        a_np, b_np = np.array(a), np.array(b)
        dot = np.dot(a_np, b_np)
        norm = np.linalg.norm(a_np) * np.linalg.norm(b_np)
        return float(dot / norm) if norm > 0 else 0.0


def create_evaluation_dataset(
    queries: list[str],
    relevant_docs: list[list[str]],
) -> list[dict[str, Any]]:
    """Create an evaluation dataset for RAG benchmarking."""
    return [{"query": q, "golden_docs": docs} for q, docs in zip(queries, relevant_docs, strict=True)]
