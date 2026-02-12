"""Vector store implementations for RAG."""

from .base import BaseVectorStore
from .in_memory_dense import InMemoryDenseVectorStore

# Backward compatibility alias
InMemoryDenseStore = InMemoryDenseVectorStore

# Optional ChromaDB dependency
try:
    from .chromadb_store import ChromaDBVectorStore
except ImportError:
    ChromaDBVectorStore = None  # type: ignore[misc,assignment]

# Optional Databricks dependency
try:
    from .databricks_store import DatabricksVectorStore
except ImportError:
    DatabricksVectorStore = None  # type: ignore[misc,assignment]

__all__ = [
    "BaseVectorStore",
    "ChromaDBVectorStore",
    "InMemoryDenseVectorStore",
    "InMemoryDenseStore",  # Backward compatibility alias
    "DatabricksVectorStore",
]
