"""Indexer package compatibility shim.

Re-exports indexing utilities from the `indexing` module for backward compatibility.
The actual implementations live in `tools.rag.indexing`.
"""

from __future__ import annotations

from typing import Any

# Re-export from the indexing module
# Using __getattr__ pattern to avoid type assignment conflicts
_exports: dict[str, Any] = {}


def _load_exports() -> None:
    """Lazy load exports from indexing module."""
    global _exports
    if _exports:
        return

    try:
        from ..indexing.indexer import (
            IndexingMetrics as _IndexingMetrics,
        )
        from ..indexing.indexer import (
            chunk_text as _chunk_text,
        )
        from ..indexing.indexer import (
            index_repository as _index_repository,
        )
        from ..indexing.indexer import (
            read_file_content as _read_file_content,
        )
        from ..indexing.indexer import (
            update_index as _update_index,
        )

        _exports["IndexingMetrics"] = _IndexingMetrics
        _exports["chunk_text"] = _chunk_text
        _exports["index_repository"] = _index_repository
        _exports["read_file_content"] = _read_file_content
        _exports["update_index"] = _update_index
    except ImportError:
        # Provide fallback implementations
        from pathlib import Path as _Path

        class _FallbackIndexingMetrics:
            """Stub for IndexingMetrics when full module not available."""

            pass

        def _fallback_chunk_text(
            text: str,
            chunk_size: int = 1000,
            overlap: int = 100,
            separator: str = "\n\n",
            max_chunk_size: int = 4000,
            min_chunk_size: int = 50,
        ) -> list[str]:
            """Split text into overlapping chunks (fallback implementation)."""
            if not text:
                return []
            chunks = []
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunks.append(text[start:end])
                start = end - overlap
            return chunks

        def _fallback_read_file_content(path: Any, max_size: int = 1024 * 1024) -> str | None:
            """Read file content (fallback implementation)."""
            p = _Path(path)
            try:
                if p.stat().st_size > max_size:
                    return None
                return p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                return None

        def _fallback_index_repository(*args: Any, **kwargs: Any) -> Any:
            """Index repository (stub - requires full indexing module)."""
            raise NotImplementedError("Full indexing module not available")

        _exports["IndexingMetrics"] = _FallbackIndexingMetrics
        _exports["chunk_text"] = _fallback_chunk_text
        _exports["index_repository"] = _fallback_index_repository
        _exports["read_file_content"] = _fallback_read_file_content

    # Also try to load semantic chunker
    try:
        from ..indexing.semantic_chunker import SemanticChunk, SemanticChunker

        _exports["SemanticChunker"] = SemanticChunker
        _exports["SemanticChunk"] = SemanticChunk
    except ImportError:
        _exports["SemanticChunker"] = None
        _exports["SemanticChunk"] = None

    # Try to load distributed indexer
    try:
        from .distributed_spark_indexer import DistributedSparkIndexer

        _exports["DistributedSparkIndexer"] = DistributedSparkIndexer
    except ImportError:
        _exports["DistributedSparkIndexer"] = None


def __getattr__(name: str) -> Any:
    """Lazy attribute access for re-exported symbols."""
    _load_exports()
    if name in _exports:
        return _exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """List available exports."""
    _load_exports()
    return list(_exports.keys()) + ["__all__"]


__all__ = [
    "chunk_text",
    "read_file_content",
    "index_repository",
    "update_index",
    "IndexingMetrics",
    "SemanticChunker",
    "SemanticChunk",
    "DistributedSparkIndexer",
]
