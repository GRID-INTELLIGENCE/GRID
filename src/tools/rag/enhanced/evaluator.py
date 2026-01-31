"""
RAG Performance Evaluator - Calculates Hit Rate and MRR.
"""
import logging
from typing import Any, Sequence

from .embeddings import EnhancedRAG

logger = logging.getLogger(__name__)

class RAGEvaluator:
    """Evaluates RAG retrieval quality."""

    def __init__(self, rag: EnhancedRAG):
        self.rag = rag

    def evaluate(self, test_set: list[dict[str, Any]], top_k: int = 5) -> dict[str, Any]:
        """
        Evaluate RAG performance on a test set.
        
        test_set: list of dicts with 'query' and 'expected_doc_ids'
        """
        total_queries = len(test_set)
        if total_queries == 0:
            return {"error": "Test set is empty"}

        hits = 0
        reciprocal_ranks = []

        for item in test_set:
            query = item["query"]
            expected_ids = set(item["expected_doc_ids"])
            
            # Perform search (hybrid search)
            results = self.rag.hybrid_search(query, top_k=top_k)
            retrieved_ids = [r["id"] for r in results]

            # Calculate Hit Rate
            is_hit = any(doc_id in expected_ids for doc_id in retrieved_ids)
            if is_hit:
                hits += 1

            # Calculate Reciprocal Rank
            rr = 0.0
            for rank, doc_id in enumerate(retrieved_ids, 1):
                if doc_id in expected_ids:
                    rr = 1.0 / rank
                    break
            reciprocal_ranks.append(rr)

        # Final metrics
        hit_rate = hits / total_queries
        mrr = sum(reciprocal_ranks) / total_queries

        metrics = {
            "total_queries": total_queries,
            "hit_rate": hit_rate,
            "mrr": mrr,
            "hits": hits,
            "top_k": top_k
        }

        logger.info(f"RAG Evaluation (top_k={top_k}): Hit Rate: {hit_rate:.2f}, MRR: {mrr:.2f}")
        return metrics
