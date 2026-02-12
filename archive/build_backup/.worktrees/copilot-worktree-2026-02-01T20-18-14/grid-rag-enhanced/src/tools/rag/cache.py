"""Query-response caching for RAG system.

Implements an LRU cache with TTL for caching RAG query responses.
Detects index changes via context hashing to avoid stale answers.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class CacheEntry:
    """A cached query response."""

    answer: str
    sources: list[dict[str, Any]]
    created_at: datetime
    context_hash: str


class QueryCache:
    """LRU cache for RAG query results with TTL support.

    Caches query responses keyed by query text, top_k, and context hash.
    Context hash includes sorted source IDs and collection count to detect
    when the index has changed and cached answers are stale.

    Environment variables:
        RAG_CACHE_ENABLED: Enable caching (default: true)
        RAG_CACHE_SIZE: Maximum cache entries (default: 100)
        RAG_CACHE_TTL: Time-to-live in seconds (default: 3600)
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600, collection_name: str = ""):
        """Initialize query cache.

        Args:
            max_size: Maximum number of entries to cache
            ttl_seconds: Time-to-live for cache entries in seconds
            collection_name: Name of the vector store collection (for cache key)
        """
        self.cache: dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        self.collection_name = collection_name

        # Stats
        self.hits = 0
        self.misses = 0

    def _make_context_hash(self, source_ids: list[str], chunk_count: int) -> str:
        """Create a hash from source IDs and chunk count to detect index changes.

        Args:
            source_ids: List of source document IDs from retrieval
            chunk_count: Total number of chunks in the collection

        Returns:
            Short hash string
        """
        sorted_ids = "|".join(sorted(source_ids))
        data = f"{self.collection_name}:{sorted_ids}:{chunk_count}"
        return hashlib.md5(data.encode()).hexdigest()[:12]

    def _make_cache_key(self, query: str, top_k: int, context_hash: str) -> str:
        """Create a unique cache key for a query.

        Args:
            query: The query text
            top_k: Number of results requested
            context_hash: Hash of the retrieval context

        Returns:
            Cache key string
        """
        data = f"{query}:{top_k}:{context_hash}"
        return hashlib.md5(data.encode()).hexdigest()

    def get(self, query: str, top_k: int, source_ids: list[str], chunk_count: int) -> dict[str, Any] | None:
        """Get a cached response if available and not expired.

        Args:
            query: The query text
            top_k: Number of results requested
            source_ids: Source IDs from retrieval (for staleness check)
            chunk_count: Total chunks in collection (for staleness check)

        Returns:
            Cached response dict with 'answer', 'sources', 'cached' keys,
            or None if not cached or expired
        """
        context_hash = self._make_context_hash(source_ids, chunk_count)
        key = self._make_cache_key(query, top_k, context_hash)

        if key in self.cache:
            entry = self.cache[key]
            now = datetime.now()
            age = now - entry.created_at

            # Check TTL
            if age < self.ttl:
                self.hits += 1
                return {
                    "answer": entry.answer,
                    "sources": entry.sources,
                    "cached": True,
                    "cache_age_seconds": age.total_seconds(),
                }

            # Expired - remove from cache
            del self.cache[key]

        self.misses += 1
        return None

    def set(
        self,
        query: str,
        top_k: int,
        source_ids: list[str],
        chunk_count: int,
        answer: str,
        sources: list[dict[str, Any]],
    ) -> None:
        """Cache a query response.

        Args:
            query: The query text
            top_k: Number of results requested
            source_ids: Source IDs from retrieval
            chunk_count: Total chunks in collection
            answer: The generated answer
            sources: The source documents
        """
        # LRU eviction if at capacity
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache, key=lambda k: self.cache[k].created_at)
            del self.cache[oldest_key]

        context_hash = self._make_context_hash(source_ids, chunk_count)
        key = self._make_cache_key(query, top_k, context_hash)

        self.cache[key] = CacheEntry(
            answer=answer, sources=sources, created_at=datetime.now(), context_hash=context_hash
        )

    def invalidate(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0.0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
            "ttl_seconds": self.ttl.total_seconds(),
        }
