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

Author: GRID AI Assistant
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "GRID AI Assistant"

from .core.config import KnowledgeBaseConfig
from .core.database import KnowledgeBaseDB
from .ingestion.pipeline import DataIngestionPipeline
from .embeddings.engine import EmbeddingEngine
from .search.retriever import VectorRetriever

__all__ = [
    "KnowledgeBaseConfig",
    "KnowledgeBaseDB",
    "DataIngestionPipeline",
    "EmbeddingEngine",
    "VectorRetriever",
]
