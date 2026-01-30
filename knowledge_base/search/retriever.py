"""
Vector Search and Retrieval Engine
===================================

Combines vector similarity search with database queries for efficient
knowledge base retrieval. Supports hybrid search and result ranking.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Iterator
from dataclasses import dataclass
from abc import ABC, abstractmethod

import numpy as np

from ..core.database import KnowledgeBaseDB, SearchResult
from ..core.config import KnowledgeBaseConfig
from ..embeddings.engine import EmbeddingEngine

logger = logging.getLogger(__name__)


@dataclass
class SearchQuery:
    """Search query configuration."""
    text: str
    limit: int = 10
    threshold: float = 0.7
    use_hybrid: bool = True
    filters: Optional[Dict[str, Any]] = None
    rerank: bool = True


@dataclass
class RankedResult:
    """Ranked search result with metadata."""
    content: str
    score: float
    metadata: Dict[str, Any]
    document_title: Optional[str] = None
    document_id: Optional[str] = None
    chunk_id: Optional[str] = None
    source_type: Optional[str] = None
    rank: int = 0


class SearchStrategy(ABC):
    """Abstract base class for search strategies."""

    @abstractmethod
    def search(self, query: SearchQuery) -> List[RankedResult]:
        """Execute search and return ranked results."""
        pass


class VectorSearchStrategy(SearchStrategy):
    """Vector similarity search strategy."""

    def __init__(self, embedding_engine: EmbeddingEngine, db: KnowledgeBaseDB):
        self.embedding_engine = embedding_engine
        self.db = db

    def search(self, query: SearchQuery) -> List[RankedResult]:
        """Search using vector similarity."""
        start_time = time.time()

        # Find similar chunks using embeddings
        similar_chunks = self.embedding_engine.search_similar(
            query.text,
            limit=query.limit * 2,  # Get more for reranking
            threshold=query.threshold
        )

        results = []
        for content, score, metadata in similar_chunks:
            # Get document info
            doc_info = self._get_document_info(metadata.get("document_id"))

            result = RankedResult(
                content=content,
                score=score,
                metadata=metadata,
                document_title=doc_info.get("title"),
                document_id=metadata.get("document_id"),
                chunk_id=metadata.get("chunk_id"),
                source_type=doc_info.get("source_type")
            )
            results.append(result)

        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)

        processing_time = time.time() - start_time
        logger.info(f"Vector search completed in {processing_time:.2f}s, found {len(results)} results")

        return results[:query.limit]

    def _get_document_info(self, document_id: Optional[str]) -> Dict[str, Any]:
        """Get document information."""
        if not document_id:
            return {}

        with self.db.session() as session:
            doc = session.query(self.db.Document).filter(
                self.db.Document.id == document_id
            ).first()

            if doc:
                return {
                    "title": doc.title,
                    "source_type": doc.source_type,
                    "created_at": doc.created_at
                }

        return {}


class KeywordSearchStrategy(SearchStrategy):
    """Keyword-based search strategy using SQL LIKE."""

    def __init__(self, db: KnowledgeBaseDB):
        self.db = db

    def search(self, query: SearchQuery) -> List[RankedResult]:
        """Search using keyword-based approach."""
        with self.db.session() as cursor:
            # Simple keyword search using LIKE
            search_term = f"%{query.text}%"
            cursor.execute("""
                SELECT c.id, c.content, c.extra_metadata, d.title
                FROM kb_chunks c
                LEFT JOIN kb_documents d ON c.document_id = d.id
                WHERE c.content LIKE ?
                ORDER BY d.created_at DESC
                LIMIT ?
            """, (search_term, query.limit))

            results = []
            for row in cursor.fetchall():
                chunk_id, content, metadata_str, doc_title = row
                metadata = json.loads(metadata_str) if metadata_str else {}

                # Simple relevance score based on term frequency
                relevance = content.lower().count(query.text.lower()) / len(content.split())

                results.append(RankedResult(
                    chunk_id=chunk_id,
                    content=content,
                    score=relevance,
                    metadata={
                        **metadata,
                        "document_title": doc_title or "Unknown",
                        "search_method": "keyword"
                    }
                ))

        return results

    def _get_document_info(self, document_id: str) -> Dict[str, Any]:
        """Get document information."""
        with self.db.session() as session:
            doc = session.query(self.db.Document).filter(
                self.db.Document.id == document_id
            ).first()

            if doc:
                return {
                    "title": doc.title,
                    "source_type": doc.source_type,
                    "created_at": doc.created_at
                }

        return {}


class HybridSearchStrategy(SearchStrategy):
    """Combines vector and keyword search for better results."""

    def __init__(self, vector_strategy: VectorSearchStrategy,
                 keyword_strategy: KeywordSearchStrategy):
        self.vector_strategy = vector_strategy
        self.keyword_strategy = keyword_strategy

    def search(self, query: SearchQuery) -> List[RankedResult]:
        """Execute hybrid search combining vector and keyword results."""
        start_time = time.time()

        # Get results from both strategies
        vector_results = self.vector_strategy.search(query)
        keyword_results = self.keyword_strategy.search(query)

        # Combine and deduplicate results
        combined_results = self._merge_results(vector_results, keyword_results, query.limit)

        # Re-rank if enabled
        if query.rerank:
            combined_results = self._rerank_results(combined_results, query)

        processing_time = time.time() - start_time
        logger.info(f"Hybrid search completed in {processing_time:.2f}s, found {len(combined_results)} results")

        return combined_results

    def _merge_results(self, vector_results: List[RankedResult],
                      keyword_results: List[RankedResult],
                      limit: int) -> List[RankedResult]:
        """Merge results from different strategies."""
        # Use a dict to deduplicate by chunk_id
        merged = {}

        # Add vector results with higher weight
        for result in vector_results:
            key = result.chunk_id or result.content[:100]
            if key not in merged:
                # Boost vector results slightly
                result.score *= 1.2
                merged[key] = result

        # Add keyword results
        for result in keyword_results:
            key = result.chunk_id or result.content[:100]
            if key not in merged:
                merged[key] = result
            else:
                # If both strategies found the same result, average the scores
                existing = merged[key]
                existing.score = (existing.score + result.score) / 2

        # Convert back to list and sort
        results = list(merged.values())
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:limit]

    def _rerank_results(self, results: List[RankedResult],
                       query: SearchQuery) -> List[RankedResult]:
        """Re-rank results using additional criteria."""
        # Simple re-ranking based on content length and position
        for result in results:
            # Prefer results with more complete sentences
            sentence_count = result.content.count('. ') + result.content.count('! ') + result.content.count('? ')
            length_bonus = min(len(result.content) / 1000, 1.0)  # Cap at 1.0

            # Boost score based on quality factors
            result.score *= (1.0 + sentence_count * 0.1 + length_bonus * 0.1)

        # Re-sort after reranking
        results.sort(key=lambda x: x.score, reverse=True)

        return results


class VectorRetriever:
    """Main search and retrieval interface."""

    def __init__(self, config: KnowledgeBaseConfig, db: KnowledgeBaseDB,
                 embedding_engine: EmbeddingEngine):
        self.config = config
        self.db = db
        self.embedding_engine = embedding_engine

        # Initialize search strategies
        self.vector_strategy = VectorSearchStrategy(embedding_engine, db)
        self.keyword_strategy = KeywordSearchStrategy(db)
        self.hybrid_strategy = HybridSearchStrategy(
            self.vector_strategy, self.keyword_strategy
        )

        # Search statistics
        self.search_stats = {
            "total_searches": 0,
            "avg_response_time": 0.0,
            "total_results_returned": 0
        }

    def search(self, query_text: str, limit: Optional[int] = None,
               use_hybrid: Optional[bool] = None, threshold: Optional[float] = None,
               filters: Optional[Dict[str, Any]] = None) -> List[RankedResult]:
        """Execute search query."""
        start_time = time.time()

        # Use config defaults if not specified
        limit = limit or self.config.search.top_k
        use_hybrid = use_hybrid if use_hybrid is not None else self.config.search.use_hybrid_search
        threshold = threshold or self.config.search.similarity_threshold

        query = SearchQuery(
            text=query_text,
            limit=limit,
            threshold=threshold,
            use_hybrid=use_hybrid,
            filters=filters,
            rerank=self.config.search.rerank_results
        )

        # Choose search strategy
        if use_hybrid:
            results = self.hybrid_strategy.search(query)
        else:
            results = self.vector_strategy.search(query)

        # Add ranking
        for i, result in enumerate(results):
            result.rank = i + 1

        # Log search query for analytics
        self.db.log_search_query(
            query=query_text,
            results_count=len(results),
            response_time=time.time() - start_time
        )

        # Update statistics
        self.search_stats["total_searches"] += 1
        self.search_stats["total_results_returned"] += len(results)

        processing_time = time.time() - start_time
        self.search_stats["avg_response_time"] = (
            (self.search_stats["avg_response_time"] * (self.search_stats["total_searches"] - 1)) +
            processing_time
        ) / self.search_stats["total_searches"]

        logger.info(f"Search completed in {processing_time:.2f}s, returned {len(results)} results")

        return results

    def search_with_sources(self, query_text: str, **kwargs) -> Dict[str, Any]:
        """Search and return results with source information."""
        results = self.search(query_text, **kwargs)

        # Group results by document
        documents = {}
        for result in results:
            doc_id = result.document_id or "unknown"
            if doc_id not in documents:
                documents[doc_id] = {
                    "title": result.document_title or "Untitled",
                    "source_type": result.source_type or "unknown",
                    "chunks": []
                }
            documents[doc_id]["chunks"].append({
                "content": result.content,
                "score": result.score,
                "rank": result.rank,
                "metadata": result.metadata
            })

        return {
            "query": query_text,
            "total_results": len(results),
            "documents": documents,
            "search_stats": self.search_stats.copy()
        }

    def get_search_stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        return {
            **self.search_stats,
            "config": {
                "default_limit": self.config.search.top_k,
                "default_threshold": self.config.search.similarity_threshold,
                "hybrid_enabled": self.config.search.use_hybrid_search,
                "reranking_enabled": self.config.search.rerank_results
            }
        }

    def clear_stats(self) -> None:
        """Clear search statistics."""
        self.search_stats = {
            "total_searches": 0,
            "avg_response_time": 0.0,
            "total_results_returned": 0
        }
        logger.info("Search statistics cleared")
