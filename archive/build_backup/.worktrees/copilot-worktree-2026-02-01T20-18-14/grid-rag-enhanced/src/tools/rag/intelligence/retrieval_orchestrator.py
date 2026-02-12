"""
Intelligent Retrieval Orchestrator for GRID RAG.

This module orchestrates the multi-stage retrieval process:
1. Hybrid Search (Dense + Sparse)
2. Multi-Hop Expansion (following references)
3. Semantic Reranking (Cross-Encoder)
"""

import logging
from typing import Any, Dict, List, Optional

from tools.rag.cross_encoder_reranker import create_cross_encoder_reranker
from tools.rag.hybrid_retriever import create_hybrid_retriever
from tools.rag.intelligence.multi_hop_retriever import create_multi_hop_retriever
from tools.rag.intelligence.query_understanding import UnderstoodQuery

logger = logging.getLogger(__name__)


class RetrievalOrchestrator:
    """
    Coordinates multi-stage retrieval to improve precision and recall.

    Stages:
    - Stage 1: Hybrid Retrieval (Vector + BM25) for broad recall.
    - Stage 2: Multi-Hop Expansion (Optional) to follow code/doc references.
    - Stage 3: Semantic Reranking (Cross-Encoder) to filter for high relevance.
    """

    def __init__(self, engine: Any):
        """
        Initialize orchestrator using components from the RAG engine.

        Args:
            engine: The RAGEngine instance containing vector store and config.
        """
        self.engine = engine
        self.config = engine.config

        # Initialize sub-retrievers
        self.hybrid = create_hybrid_retriever(
            vector_store=engine.vector_store, embedding_provider=engine.embedding_provider, config=self.config
        )

        # Multi-hop relies on a base retriever (hybrid or vector)
        base_retriever = self.hybrid if self.hybrid else engine
        self.multi_hop = create_multi_hop_retriever(base_retriever=base_retriever, config=self.config)

        # Cross-Encoder for precision reranking
        self.reranker = create_cross_encoder_reranker(config=self.config)

        logger.info("RetrievalOrchestrator initialized with Multi-Stage Pipeline.")

    async def retrieve(self, understood: UnderstoodQuery, top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute the intelligent retrieval pipeline.

        Args:
            understood: The structured query from the intelligence layer.
            top_k: Number of results to return.

        Returns:
            Dictionary with documents, metadatas, distances, and metrics.
        """
        k = top_k or self.config.top_k
        query = understood.original_query

        # Determine if we should use expanded queries from understanding
        search_query = understood.expanded_queries[0] if understood.expanded_queries else query

        logger.info(f"Starting retrieval for query: '{search_query}' (Intent: {understood.intent.value})")

        # --- Stage 1 & 2: Retrieval & Expansion ---
        # If multi-hop is enabled, it handles its own call to the base retriever
        if self.config.multi_hop_enabled:
            results = await self.multi_hop.async_retrieve(search_query, top_k=k * 2)
        elif self.hybrid:
            results = await self.hybrid.async_search(search_query, top_k=k * 2)
        else:
            # Fallback to standard vector search
            query_embedding = await self.engine.embedding_provider.async_embed(search_query)
            results = await self.engine.vector_store.async_query(query_embedding=query_embedding, n_results=k * 2)

        # --- Stage 3: Semantic Reranking ---
        if self.reranker and results.get("documents"):
            logger.info(f"Reranking {len(results['documents'])} candidates...")

            reranked_indices = await self.reranker.async_rerank(query=query, documents=results["documents"], top_k=k)

            # Reconstruct results in reranked order
            new_ids = []
            new_docs = []
            new_metas = []
            new_dists = []

            for idx, score in reranked_indices:
                new_ids.append(results["ids"][idx])
                new_docs.append(results["documents"][idx])
                new_metas.append(results["metadatas"][idx])
                # Cross-encoder scores vary, we normalize/invert for distance consistency
                new_dists.append(1.0 - (score / 10.0) if score <= 10 else 0.0)

            results.update(
                {
                    "ids": new_ids,
                    "documents": new_docs,
                    "metadatas": new_metas,
                    "distances": new_dists,
                    "reranked": True,
                }
            )

        # Truncate to final top_k
        for key in ["ids", "documents", "metadatas", "distances"]:
            if key in results:
                results[key] = results[key][:k]

        return results


def create_retrieval_orchestrator(engine: Any) -> RetrievalOrchestrator:
    """Factory function for retrieval orchestrator."""
    return RetrievalOrchestrator(engine=engine)
