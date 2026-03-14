"""
GRID Knowledge Base System
==========================

A modern, efficient RAG (Retrieval-Augmented Generation) system built on Databricks.

Features:
- Multi-modal data ingestion
- Vector embeddings with hybrid search
- LLM integration for generation
- REST API with monitoring
- Security and access controls
- Scalable architecture

Provider note: This package uses the OpenAI API only for embeddings and LLM
(OPENAI_ATLAS_API / OPENAI_API_KEY required). For multi-provider RAG including
local Ollama, Anthropic, or OpenAI-compatible endpoints, use the main RAG stack
under ``src/tools/rag``.

Author: GRID AI Assistant
Version: 1.0.0
"""

from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__ = "1.0.0"
__author__ = "GRID AI Assistant"

if TYPE_CHECKING:
    from .core.config import KnowledgeBaseConfig
    from .core.database import KnowledgeBaseDB
    from .embeddings.engine import EmbeddingEngine
    from .ingestion.pipeline import DataIngestionPipeline
    from .search.retriever import VectorRetriever

__all__ = [
    "KnowledgeBaseConfig",
    "KnowledgeBaseDB",
    "DataIngestionPipeline",
    "EmbeddingEngine",
    "VectorRetriever",
]


_LAZY_EXPORTS = {
    "KnowledgeBaseConfig": ("knowledge_base.core.config", "KnowledgeBaseConfig"),
    "KnowledgeBaseDB": ("knowledge_base.core.database", "KnowledgeBaseDB"),
    "DataIngestionPipeline": ("knowledge_base.ingestion.pipeline", "DataIngestionPipeline"),
    "EmbeddingEngine": ("knowledge_base.embeddings.engine", "EmbeddingEngine"),
    "VectorRetriever": ("knowledge_base.search.retriever", "VectorRetriever"),
}


def __getattr__(name: str) -> Any:
    """Lazily import heavyweight knowledge-base components on first access."""
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, symbol_name = _LAZY_EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, symbol_name)
    globals()[name] = value
    return value
