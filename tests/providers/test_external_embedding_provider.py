"""Tests for external embedding providers (Mistral, OpenAI)."""

import os

import pytest

from tools.rag.embeddings.factory import EmbeddingProviderType, get_embedding_provider


def test_get_embedding_provider_mistral_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """RAG_EMBEDDING_PROVIDER=mistral + MISTRAL_API_KEY → MistralEmbeddingProvider."""
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key-for-mistral-embedding-unit-test")

    from tools.rag.config import RAGConfig

    config = RAGConfig(embedding_provider="mistral", embedding_model="mistral-embed")
    provider = get_embedding_provider(provider_type="mistral", config=config)
    assert type(provider).__name__ == "MistralEmbeddingProvider"


def test_get_embedding_provider_mistral_raises_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """RAG_EMBEDDING_PROVIDER=mistral without MISTRAL_API_KEY → ValueError."""
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    from tools.rag.config import RAGConfig

    config = RAGConfig(embedding_provider="mistral", embedding_model="mistral-embed")
    with pytest.raises(ValueError, match="MISTRAL_API_KEY"):
        get_embedding_provider(provider_type="mistral", config=config)


def test_embedding_provider_type_includes_mistral() -> None:
    """EmbeddingProviderType enum includes MISTRAL."""
    assert hasattr(EmbeddingProviderType, "MISTRAL")
    assert EmbeddingProviderType.MISTRAL.value == "mistral"


def test_mistral_embedding_provider_dimension() -> None:
    """MistralEmbeddingProvider.dimension returns 1024 as the fallback default."""
    from unittest.mock import patch

    from tools.rag.embeddings.mistral import MistralEmbeddingProvider

    provider = MistralEmbeddingProvider.__new__(MistralEmbeddingProvider)
    provider.model = "mistral-embed"
    provider.api_key = "fake-key"
    provider.timeout = 60
    provider._dimension = None
    provider._client_instance = None

    from unittest.mock import MagicMock

    breaker_mock = MagicMock()
    breaker_mock.__enter__ = MagicMock(return_value=None)
    breaker_mock.__exit__ = MagicMock(return_value=False)
    provider._breaker = breaker_mock

    # Force embed to raise so dimension falls back to 1024
    with patch.object(provider, "embed", side_effect=RuntimeError("no API in tests")):
        assert provider.dimension == 1024
