"""
XAI Integration Module for GRID

Provides comprehensive XAI streaming, threading, performance optimization,
and adaptive processing capabilities for enhanced XAI interactions.
"""

from .explainer import XAIExplainer, explainer
from .performance_optimizer import XAICache, adaptive_processor, cache, load_balancer
from .stream_adapter import XAIStreamAdapter
from .threading_framework import WorkerStats, WorkerThread, XAIThreadPool, resource_manager, thread_pool
from .vector_store import (
    BaseEmbedding,
    ChromaDenseVectorStore,
    DenseVectorStore,
    InMemoryDenseVectorStore,
    SimpleEmbedding,
    VectorStoreFactory,
)

__all__ = [
    "XAIExplainer",
    "explainer",
    "XAIStreamAdapter",
    "stream_adapter",
    "XAIThreadPool",
    "thread_pool",
    "WorkerThread",
    "WorkerStats",
    "resource_manager",
    "XAICache",
    "cache",
    "XAILoadBalancer",
    "load_balancer",
    "XAIAdaptiveProcessor",
    "adaptive_processor",
    "BaseEmbedding",
    "SimpleEmbedding",
    "DenseVectorStore",
    "InMemoryDenseVectorStore",
    "ChromaDenseVectorStore",
    "VectorStoreFactory",
]
