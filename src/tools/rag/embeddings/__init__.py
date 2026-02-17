"""Embedding providers for RAG."""

from .base import BaseEmbeddingProvider
from .factory import EmbeddingProviderType, get_embedding_provider
from .huggingface import HuggingFaceEmbeddingProvider
from .nomic_v2 import OllamaEmbeddingProvider
from .simple import SimpleEmbedding, SimpleEmbeddings

# OpenAI provider (optional dependency)
try:
    from .openai import OpenAIEmbeddingProvider
except ImportError:
    OpenAIEmbeddingProvider = None  # type: ignore

# Test provider (for testing only - NOT for production)
from .test_provider import TestEmbeddingProvider, get_test_provider

__all__ = [
    "BaseEmbeddingProvider",
    "OllamaEmbeddingProvider",
    "HuggingFaceEmbeddingProvider",
    "SimpleEmbedding",
    "SimpleEmbeddings",
    "TestEmbeddingProvider",
    "get_embedding_provider",
    "get_test_provider",
    "EmbeddingProviderType",
]

# Add OpenAI if available
if OpenAIEmbeddingProvider is not None:
    __all__.append("OpenAIEmbeddingProvider")
