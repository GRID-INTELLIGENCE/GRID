"""Vector store registry for pluggable backend management.

This registry provides a factory pattern for creating and managing
vector store backends, making it easy to add new backends without
modifying existing code.
"""

from __future__ import annotations

import logging
from typing import Any

from .base import BaseVectorStore

logger = logging.getLogger(__name__)


class VectorStoreRegistry:
    """Registry for vector store backends."""

    _backends: dict[str, type[BaseVectorStore]] = {}

    @classmethod
    def register(cls, name: str, backend_class: type[BaseVectorStore]) -> None:
        """Register a new vector store backend.

        Args:
            name: Unique name for the backend (e.g., 'chromadb', 'databricks')
            backend_class: Class implementing BaseVectorStore interface

        Raises:
            ValueError: If backend name already registered
        """
        if name in cls._backends:
            raise ValueError(f"Backend '{name}' is already registered")

        if not issubclass(backend_class, BaseVectorStore):
            raise TypeError("Backend class must inherit from BaseVectorStore")

        cls._backends[name] = backend_class
        logger.info(f"Registered vector store backend: {name}")

    @classmethod
    def unregister(cls, name: str) -> None:
        """Unregister a vector store backend.

        Args:
            name: Name of backend to unregister
        """
        if name in cls._backends:
            del cls._backends[name]
            logger.info(f"Unregistered vector store backend: {name}")

    @classmethod
    def get_backend_class(cls, name: str) -> type[BaseVectorStore] | None:
        """Get registered backend class by name.

        Args:
            name: Name of the backend

        Returns:
            Backend class if registered, None otherwise
        """
        return cls._backends.get(name)

    @classmethod
    def create(cls, provider: str, **kwargs: Any) -> BaseVectorStore:
        """Create a vector store instance using registered backend.

        Args:
            provider: Name of the backend provider
            **kwargs: Arguments passed to backend constructor

        Returns:
            Initialized vector store instance

        Raises:
            ValueError: If provider not registered
            RuntimeError: If backend initialization fails
        """
        provider = provider.lower()
        backend_class = cls.get_backend_class(provider)

        if backend_class is None:
            available = ", ".join(cls.list_backends())
            raise ValueError(
                f"Unknown vector store provider: '{provider}'. "
                f"Available: {available}"
            )

        try:
            logger.info(f"Creating vector store with provider: {provider}")
            return backend_class(**kwargs)
        except Exception as e:
            logger.error(f"Failed to create vector store '{provider}': {e}")
            raise RuntimeError(f"Failed to initialize vector store: {e}") from e

    @classmethod
    def list_backends(cls) -> list[str]:
        """List all registered backends.

        Returns:
            List of registered backend names
        """
        return sorted(cls._backends.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a backend is registered.

        Args:
            name: Name of the backend

        Returns:
            True if registered, False otherwise
        """
        return name.lower() in cls._backends


# Auto-register built-in backends
def _register_builtins() -> None:
    """Register built-in vector store backends."""
    try:
        from .chromadb_store import ChromaDBVectorStore

        VectorStoreRegistry.register("chromadb", ChromaDBVectorStore)
    except ImportError:
        logger.debug("ChromaDB not available, skipping registration")

    try:
        from .databricks_store import DatabricksVectorStore

        VectorStoreRegistry.register("databricks", DatabricksVectorStore)
    except ImportError:
        logger.debug("Databricks SQL connector not available, skipping registration")

    try:
        from .in_memory_dense import InMemoryDenseVectorStore

        VectorStoreRegistry.register("in_memory", InMemoryDenseVectorStore)
    except ImportError:
        logger.debug("In-memory vector store not available, skipping registration")


# Register built-in backends on module load
_register_builtins()
