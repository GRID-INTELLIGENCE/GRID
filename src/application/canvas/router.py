"""Unified Router - Routes through GRID's multi-directory structure with similarity matching."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from .schemas import RouteResult, ScoredRoute, SimilarityMatch

logger = logging.getLogger(__name__)


class UnifiedRouter:
    """Routes through GRID's multi-directory structure with similarity matching."""

    def __init__(
        self,
        workspace_root: Path,
        rag_system: Any | None = None,
        vector_store: Any | None = None,
    ):
        """Initialize unified router.

        Args:
            workspace_root: Root path of the workspace
            rag_system: Optional RAG system for embeddings
            vector_store: Optional vector store for similarity search
        """
        self.workspace_root = Path(workspace_root)
        self.rag_system = rag_system
        self.vector_store = vector_store
        self._directory_index: dict[str, dict[str, Any]] = {}
        self._route_cache: dict[str, RouteResult] = {}

    async def route_query(
        self,
        query: str,
        context: dict[str, Any] | None = None,
        max_results: int = 5,
    ) -> RouteResult:
        """Route query to relevant directories/files using similarity matching.

        Args:
            query: Query string to route
            context: Optional context dictionary
            max_results: Maximum number of results to return

        Returns:
            RouteResult with scored routes
        """
        # Check cache
        cache_key = f"{query}:{max_results}"
        if cache_key in self._route_cache:
            return self._route_cache[cache_key]

        # Find similar items using directory scanning and keyword matching
        similar_items = await self._find_similar(query, context, max_results * 2)

        # Score routes by metrics
        scored_routes = self._score_routes(similar_items, query, context)

        # Return top routes
        result = RouteResult(
            query=query,
            routes=scored_routes[:max_results],
            confidence=self._calculate_confidence(scored_routes),
            total_candidates=len(similar_items),
        )

        # Cache result
        self._route_cache[cache_key] = result
        return result

    async def _find_similar(
        self,
        query: str,
        context: dict[str, Any] | None,
        max_results: int,
    ) -> list[SimilarityMatch]:
        """Find similar directories/files to the query.

        Uses directory structure analysis and keyword matching.
        If RAG system is available, uses vector similarity.

        Args:
            query: Query string
            context: Optional context
            max_results: Maximum results to return

        Returns:
            List of SimilarityMatch objects
        """
        matches: list[SimilarityMatch] = []
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Key directories to check
        key_directories = [
            "grid",
            "application",
            "light_of_the_seven",
            "tools",
            "Arena",
        ]

        for dir_name in key_directories:
            dir_path = self.workspace_root / dir_name
            if not await asyncio.to_thread(dir_path.exists):
                continue

            # Calculate similarity based on directory name and content
            similarity = self._calculate_directory_similarity(dir_path, query_words)

            if similarity > 0.1:  # Threshold
                matches.append(
                    SimilarityMatch(
                        path=dir_path,
                        similarity=similarity,
                        metadata={
                            "type": "directory",
                            "name": dir_name,
                            "depth": len(dir_path.parts) - len(self.workspace_root.parts),
                        },
                    )
                )

                # Look for specific files that match
                try:
                    py_files = await asyncio.to_thread(lambda dp=dir_path: [
                        fp for fp in dp.rglob("*.py") if fp.is_file()
                    ])
                    for file_path in py_files:
                        if True:
                            file_similarity = self._calculate_file_similarity(file_path, query_words)
                            if file_similarity > 0.2:
                                matches.append(
                                    SimilarityMatch(
                                        path=file_path,
                                        similarity=file_similarity,
                                        metadata={
                                            "type": "file",
                                            "name": file_path.name,
                                            "parent": dir_name,
                                        },
                                    )
                                )
                except Exception as e:
                    logger.debug(f"Error scanning {dir_path}: {e}")

        # Sort by similarity and limit
        matches.sort(key=lambda m: m.similarity, reverse=True)
        return matches[:max_results]

    def _calculate_directory_similarity(self, dir_path: Path, query_words: set[str]) -> float:
        """Calculate similarity between directory and query.

        Args:
            dir_path: Directory path
            query_words: Set of query words

        Returns:
            Similarity score (0.0 to 1.0)
        """
        dir_name_lower = dir_path.name.lower()
        dir_words = set(dir_name_lower.split("_"))

        # Exact word matches
        matches = query_words.intersection(dir_words)
        if not matches:
            return 0.0

        # Calculate Jaccard similarity
        union = query_words.union(dir_words)
        similarity = len(matches) / len(union) if union else 0.0

        # Boost for common prefixes
        for q_word in query_words:
            if dir_name_lower.startswith(q_word) or q_word in dir_name_lower:
                similarity += 0.2

        return min(1.0, similarity)

    def _calculate_file_similarity(self, file_path: Path, query_words: set[str]) -> float:
        """Calculate similarity between file and query.

        Args:
            file_path: File path
            query_words: Set of query words

        Returns:
            Similarity score (0.0 to 1.0)
        """
        file_name_lower = file_path.stem.lower()
        file_words = set(file_name_lower.split("_"))

        # Exact word matches
        matches = query_words.intersection(file_words)
        if not matches:
            return 0.0

        # Calculate similarity
        union = query_words.union(file_words)
        similarity = len(matches) / len(union) if union else 0.0

        # Boost for exact matches in filename
        if any(q_word == file_name_lower for q_word in query_words):
            similarity += 0.3

        return min(1.0, similarity)

    def _score_routes(
        self,
        candidates: list[SimilarityMatch],
        query: str,
        context: dict[str, Any] | None,
    ) -> list[ScoredRoute]:
        """Score routes using multi-factor relevance metrics.

        Args:
            candidates: List of similarity matches
            query: Original query
            context: Optional context

        Returns:
            List of scored routes, sorted by final score
        """
        scored: list[ScoredRoute] = []

        for candidate in candidates:
            # Base similarity score
            similarity_score = candidate.similarity

            # Path complexity penalty (prefer simpler paths)
            complexity_penalty = self._calculate_complexity_penalty(candidate.path)

            # Context relevance boost
            context_boost = self._calculate_context_boost(candidate, context)

            # Final score: weighted combination
            final_score = similarity_score * 0.6 + (1.0 - complexity_penalty) * 0.2 + context_boost * 0.2

            scored.append(
                ScoredRoute(
                    path=candidate.path,
                    similarity=similarity_score,
                    complexity_penalty=complexity_penalty,
                    context_boost=context_boost,
                    final_score=final_score,
                    metadata=candidate.metadata,
                )
            )

        # Sort by final score
        return sorted(scored, key=lambda r: r.final_score, reverse=True)

    def _calculate_complexity_penalty(self, path: Path) -> float:
        """Calculate complexity penalty for a path.

        Args:
            path: Path to analyze

        Returns:
            Complexity penalty (0.0 = simple, 1.0 = very complex)
        """
        # Depth penalty
        depth = len(path.parts) - len(self.workspace_root.parts)
        depth_penalty = min(1.0, depth / 10.0)

        # Name length penalty (longer names = more complex)
        name_length = len(path.name)
        name_penalty = min(1.0, name_length / 50.0)

        # Combine penalties
        return depth_penalty * 0.7 + name_penalty * 0.3

    def _calculate_context_boost(self, candidate: SimilarityMatch, context: dict[str, Any] | None) -> float:
        """Calculate context boost for a candidate.

        Args:
            candidate: Similarity match candidate
            context: Optional context

        Returns:
            Context boost score (0.0 to 1.0)
        """
        if not context:
            return 0.5  # Neutral

        boost = 0.5

        # Check if context mentions the path type
        context_str = str(context).lower()
        path_type = candidate.metadata.get("type", "")
        if path_type in context_str:
            boost += 0.2

        # Check if parent directory is mentioned
        parent = candidate.metadata.get("parent", "")
        if parent and parent in context_str:
            boost += 0.3

        return min(1.0, boost)

    def _calculate_confidence(self, scored_routes: list[ScoredRoute]) -> float:
        """Calculate overall confidence in routing results.

        Args:
            scored_routes: List of scored routes

        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not scored_routes:
            return 0.0

        # Confidence based on top score and score distribution
        top_score = scored_routes[0].final_score
        score_range = (
            scored_routes[0].final_score - scored_routes[-1].final_score if len(scored_routes) > 1 else top_score
        )

        # High top score and good separation = high confidence
        confidence = top_score * 0.7 + min(1.0, score_range * 2) * 0.3

        return confidence

    def clear_cache(self) -> None:
        """Clear route cache."""
        self._route_cache.clear()
