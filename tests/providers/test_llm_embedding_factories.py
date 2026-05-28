"""Tests for get_llm_client() and get_embedding_client() factory functions."""

import os

import pytest


def test_get_llm_client_returns_ollama_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without GRID_LLM_PROVIDER or MISTRAL_API_KEY, returns OllamaNativeClient."""
    monkeypatch.delenv("GRID_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    from grid.services.llm.llm_client import OllamaNativeClient, get_llm_client

    client = get_llm_client()
    assert isinstance(client, OllamaNativeClient)


def test_get_llm_client_returns_mistral_when_provider_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """GRID_LLM_PROVIDER=mistral + MISTRAL_API_KEY → MistralNativeClient."""
    monkeypatch.setenv("GRID_LLM_PROVIDER", "mistral")
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key-factory-unit-test")

    from grid.services.llm.llm_client import MistralNativeClient, get_llm_client

    client = get_llm_client()
    assert isinstance(client, MistralNativeClient)


def test_get_llm_client_falls_back_to_ollama_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """GRID_LLM_PROVIDER=mistral but no key → falls back to OllamaNativeClient."""
    monkeypatch.setenv("GRID_LLM_PROVIDER", "mistral")
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    from grid.services.llm.llm_client import OllamaNativeClient, get_llm_client

    client = get_llm_client()
    assert isinstance(client, OllamaNativeClient)


def test_get_embedding_client_returns_ollama_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without GRID_EMBEDDING_PROVIDER, returns OllamaEmbeddingClient."""
    monkeypatch.delenv("GRID_EMBEDDING_PROVIDER", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    from grid.services.embeddings.embedding_client import OllamaEmbeddingClient, get_embedding_client

    client = get_embedding_client()
    assert isinstance(client, OllamaEmbeddingClient)


def test_get_embedding_client_returns_mistral_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """GRID_EMBEDDING_PROVIDER=mistral + MISTRAL_API_KEY → MistralEmbeddingClient."""
    monkeypatch.setenv("GRID_EMBEDDING_PROVIDER", "mistral")
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key-embedding-unit-test")

    from grid.services.embeddings.embedding_client import MistralEmbeddingClient, get_embedding_client

    client = get_embedding_client()
    assert isinstance(client, MistralEmbeddingClient)


def test_get_embedding_client_falls_back_to_ollama_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """GRID_EMBEDDING_PROVIDER=mistral but no key → falls back to OllamaEmbeddingClient."""
    monkeypatch.setenv("GRID_EMBEDDING_PROVIDER", "mistral")
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    from grid.services.embeddings.embedding_client import OllamaEmbeddingClient, get_embedding_client

    client = get_embedding_client()
    assert isinstance(client, OllamaEmbeddingClient)
