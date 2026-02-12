"""Information chunking for organizing data into manageable units."""

from collections.abc import Callable
from typing import Any

from ..schemas.user_cognitive_profile import UserCognitiveProfile


class InformationChunker:
    """Chunks information into manageable units for working memory.

    Organizes information following Miller's 7±2 principle.
    """

    def __init__(self, default_chunk_size: int = 5):
        """Initialize the information chunker.

        Args:
            default_chunk_size: Default number of items per chunk
        """
        self.default_chunk_size = default_chunk_size

    def chunk(
        self, items: list[Any], user_profile: UserCognitiveProfile | None = None, max_chunks: int | None = None
    ) -> list[list[Any]]:
        """Chunk a list of items into manageable groups.

        Args:
            items: List of items to chunk
            user_profile: Optional user cognitive profile
            max_chunks: Optional maximum number of chunks

        Returns:
            List of chunks (each chunk is a list of items)
        """
        # Determine chunk size based on user capacity
        chunk_size = self.default_chunk_size
        if user_profile:
            # Adjust based on working memory capacity
            capacity = user_profile.working_memory_capacity
            chunk_size = int(7 * capacity)  # Scale Miller's 7±2 by capacity

        # Limit chunk size to reasonable bounds
        chunk_size = max(3, min(9, chunk_size))

        # Chunk the items
        chunks = []
        for i in range(0, len(items), chunk_size):
            chunk = items[i : i + chunk_size]
            chunks.append(chunk)

        # Limit number of chunks if specified
        if max_chunks and len(chunks) > max_chunks:
            # Merge smaller chunks or truncate
            chunks = chunks[:max_chunks]

        return chunks

    def chunk_by_similarity(
        self, items: list[dict[str, Any]], similarity_key: str, user_profile: UserCognitiveProfile | None = None
    ) -> list[list[dict[str, Any]]]:
        """Chunk items by similarity.

        Args:
            items: List of items with similarity attributes
            similarity_key: Key to use for similarity grouping
            user_profile: Optional user cognitive profile

        Returns:
            List of chunks grouped by similarity
        """
        if not items:
            return []

        # Group by similarity
        groups: dict[str, list[dict[str, Any]]] = {}
        for item in items:
            similarity_value = item.get(similarity_key, "other")
            if similarity_value not in groups:
                groups[similarity_value] = []
            groups[similarity_value].append(item)

        # Chunk each group
        chunks = []
        for group_items in groups.values():
            group_chunks = self.chunk(group_items, user_profile)
            chunks.extend(group_chunks)

        return chunks

    def chunk_hierarchically(
        self,
        items: list[dict[str, Any]],
        hierarchy_levels: list[str],
        user_profile: UserCognitiveProfile | None = None,
    ) -> dict[str, Any]:
        """Chunk items hierarchically by multiple levels.

        Args:
            items: List of items to chunk
            hierarchy_levels: List of keys for hierarchical grouping
            user_profile: Optional user cognitive profile

        Returns:
            Hierarchical chunk structure
        """
        if not hierarchy_levels:
            # No hierarchy, just chunk normally
            return {
                "chunks": self.chunk(items, user_profile),
                "level": "flat",
            }

        # Group by first level
        first_level = hierarchy_levels[0]
        groups: dict[str, list[dict[str, Any]]] = {}
        for item in items:
            level_value = item.get(first_level, "other")
            if level_value not in groups:
                groups[level_value] = []
            groups[level_value].append(item)

        # Recursively chunk each group
        result: dict[str, Any] = {
            "level": first_level,
            "groups": {},
        }

        for group_key, group_items in groups.items():
            if len(hierarchy_levels) > 1:
                # Recurse with remaining levels
                result["groups"][group_key] = self.chunk_hierarchically(group_items, hierarchy_levels[1:], user_profile)
            else:
                # Final level, chunk the items
                result["groups"][group_key] = {
                    "chunks": self.chunk(group_items, user_profile),
                    "level": "items",
                }

        return result

    def create_chunk_summary(
        self, chunk: list[Any], summary_func: Callable[[list[Any]], dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Create a summary for a chunk.

        Args:
            chunk: Chunk of items
            summary_func: Optional function to create summary

        Returns:
            Dictionary with chunk summary
        """
        if summary_func:
            summary = summary_func(chunk)
        else:
            # Default summary
            summary = {
                "count": len(chunk),
                "type": type(chunk[0]).__name__ if chunk else "empty",
            }

        return {
            "summary": summary,
            "items": chunk,
            "count": len(chunk),
        }
