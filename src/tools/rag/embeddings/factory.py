"""Factory for creating embedding providers.

Supports two resolution paths:
1. **Fallback chain** (default): Load config/ollama-models.json, probe providers
   in order, return the first healthy one. Same activation rules as the LLM factory.
2. **Legacy explicit mode**: RAG_EMBEDDING_PROVIDER env var picks a single provider.
"""

import logging
import os
from enum import StrEnum

from ..config import RAGConfig
from .base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


class EmbeddingProviderType(StrEnum):
    """Types of embedding providers."""

    OLLAMA = "ollama"  # Ollama-based models (Nomic, etc.)
    HUGGINGFACE = "huggingface"  # Local HF models (BGE, etc.)
    OPENAI = "openai"  # OpenAI cloud embeddings
    SIMPLE = "simple"  # Simple fallback (word frequency)


def _use_fallback_chain() -> bool:
    """Check whether to use the ollama-models.json fallback chain for embeddings."""
    mode = os.environ.get("RAG_EMBEDDING_MODE", "").lower()
    if mode == "auto":
        return True
    if not mode:
        try:
            from ..model_resolver import _find_config_path

            _find_config_path()
            return True
        except FileNotFoundError:
            return False
    return False


def _embedding_from_resolved(resolved: "ResolvedProvider") -> BaseEmbeddingProvider:  # noqa: F821
    """Instantiate an embedding provider from a ResolvedProvider."""
    if resolved.type in ("ollama-cloud", "ollama-local"):
        from .nomic_v2 import OllamaEmbeddingProvider

        return OllamaEmbeddingProvider(
            model=resolved.model,
            base_url=resolved.url or "http://localhost:11434",
        )
    if resolved.type == "openai":
        from .openai import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(model=resolved.model)
    if resolved.type == "simple":
        from .simple import SimpleEmbedding

        return SimpleEmbedding()

    msg = f"Unsupported resolved embedding provider type: {resolved.type}"
    raise ValueError(msg)


def get_embedding_provider(provider_type: str | None = None, config: RAGConfig | None = None) -> BaseEmbeddingProvider:
    """Get an embedding provider with fallback-chain or legacy explicit selection.

    Args:
        provider_type: Type of provider (default: nomic-v2)
        config: RAG configuration (optional)

    Returns:
        Embedding provider instance
    """
    # --- Fallback chain path ---
    if provider_type is None and _use_fallback_chain():
        from ..model_resolver import resolve_embedding

        resolved = resolve_embedding()
        logger.info("embedding_factory.fallback_chain", provider=resolved.label, model=resolved.model)
        return _embedding_from_resolved(resolved)

    # --- Legacy explicit-mode path ---
    if config is None:
        config = RAGConfig.from_env()

    if provider_type is None:
        provider_type = config.embedding_provider if config else EmbeddingProviderType.HUGGINGFACE.value

    provider_type = provider_type.lower()

    if provider_type == "test":
        raise ValueError(
            "Test embedding provider cannot be used via factory in production code. "
            "Import directly from tools.rag.embeddings.test_provider in test modules only."
        )

    if provider_type == EmbeddingProviderType.OLLAMA.value:
        from .nomic_v2 import OllamaEmbeddingProvider

        return OllamaEmbeddingProvider(model=config.embedding_model, base_url=config.ollama_base_url)
    elif provider_type == EmbeddingProviderType.HUGGINGFACE.value:
        try:
            from .huggingface import HuggingFaceEmbeddingProvider
        except ImportError as e:
            raise ImportError(
                "HuggingFace embedding provider is not available (numpy or sentence-transformers "
                "may be missing or broken). Use provider_type='ollama' or 'simple', or fix the "
                "environment. Original error: " + str(e)
            ) from e
        return HuggingFaceEmbeddingProvider(
            model_name=config.embedding_model,
            allow_download=getattr(config, "reranker_allow_download", False),
        )
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
