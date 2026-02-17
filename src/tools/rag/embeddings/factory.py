"""Factory for creating embedding providers."""

from enum import StrEnum

from ..config import RAGConfig
from .base import BaseEmbeddingProvider


class EmbeddingProviderType(StrEnum):
    """Types of embedding providers."""

    OLLAMA = "ollama"  # Ollama-based models (Nomic, etc.)
    HUGGINGFACE = "huggingface"  # Local HF models (BGE, etc.)
    OPENAI = "openai"  # OpenAI cloud embeddings
    SIMPLE = "simple"  # Simple fallback (word frequency)


def get_embedding_provider(provider_type: str | None = None, config: RAGConfig | None = None) -> BaseEmbeddingProvider:
    """Get an embedding provider.

    Args:
        provider_type: Type of provider (default: nomic-v2)
        config: RAG configuration (optional)

    Returns:
        Embedding provider instance
    """
    if config is None:
        config = RAGConfig.from_env()

    if provider_type is None:
        provider_type = config.embedding_provider if config else EmbeddingProviderType.HUGGINGFACE.value

    provider_type = provider_type.lower()

    if provider_type == EmbeddingProviderType.OLLAMA.value:
        from .nomic_v2 import OllamaEmbeddingProvider

        return OllamaEmbeddingProvider(model=config.embedding_model, base_url=config.ollama_base_url)
    elif provider_type == EmbeddingProviderType.HUGGINGFACE.value:
        from .huggingface import HuggingFaceEmbeddingProvider

        return HuggingFaceEmbeddingProvider(model_name=config.embedding_model)
    elif provider_type == EmbeddingProviderType.OPENAI.value:
        from .openai import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(model=config.embedding_model)
    elif provider_type == EmbeddingProviderType.SIMPLE.value:
        from .simple import SimpleEmbedding

        return SimpleEmbedding()
    else:
        raise ValueError(
            f"Unknown embedding provider type: {provider_type}. "
            f"Available: {', '.join([e.value for e in EmbeddingProviderType])}"
        )
