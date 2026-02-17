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

__all__ = [
    "BaseEmbeddingProvider",
    "OllamaEmbeddingProvider",
    "HuggingFaceEmbeddingProvider",
    "SimpleEmbedding",
    "SimpleEmbeddings",
    "get_embedding_provider",
    "EmbeddingProviderType",
]

# Add OpenAI if available
if OpenAIEmbeddingProvider is not None:
    __all__.append("OpenAIEmbeddingProvider")
