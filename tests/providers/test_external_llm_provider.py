"""Tests for external LLM providers (OpenAI, Anthropic, Gemini, OpenAI-compatible)."""

import os

import pytest

from tools.rag.config import ModelMode, RAGConfig
from tools.rag.llm.factory import LLMProviderType, get_llm_provider


def test_get_llm_provider_openai_when_configured() -> None:
    """When RAG_LLM_MODE=external and RAG_LLM_PROVIDER=openai and OPENAI_API_KEY set, return OpenAILLM."""
    os.environ["RAG_LLM_MODE"] = "external"
    os.environ["RAG_LLM_PROVIDER"] = "openai"
    os.environ["OPENAI_API_KEY"] = "sk-test-key-for-unit-test"
    try:
        config = RAGConfig.from_env()
        assert config.llm_mode == ModelMode.EXTERNAL
        assert config.external_provider == "openai"
        provider = get_llm_provider(config=config)
        assert type(provider).__name__ == "OpenAILLM"
    finally:
        os.environ.pop("RAG_LLM_MODE", None)
        os.environ.pop("RAG_LLM_PROVIDER", None)
        os.environ.pop("OPENAI_API_KEY", None)


def test_get_llm_provider_anthropic_when_configured() -> None:
    """When RAG_LLM_MODE=external and RAG_LLM_PROVIDER=anthropic and ANTHROPIC_API_KEY set, return AnthropicLLM."""
    os.environ["RAG_LLM_MODE"] = "external"
    os.environ["RAG_LLM_PROVIDER"] = "anthropic"
    os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-key-for-unit-test"
    try:
        config = RAGConfig.from_env()
        assert config.llm_mode == ModelMode.EXTERNAL
        provider = get_llm_provider(config=config)
        assert type(provider).__name__ == "AnthropicLLM"
    finally:
        os.environ.pop("RAG_LLM_MODE", None)
        os.environ.pop("RAG_LLM_PROVIDER", None)
        os.environ.pop("ANTHROPIC_API_KEY", None)


def test_get_llm_provider_openai_raises_without_key() -> None:
    """When external provider is openai but OPENAI_API_KEY missing, raise ValueError."""
    os.environ["RAG_LLM_MODE"] = "external"
    os.environ["RAG_LLM_PROVIDER"] = "openai"
    os.environ.pop("OPENAI_API_KEY", None)
    try:
        config = RAGConfig.from_env()
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            get_llm_provider(config=config)
    finally:
        os.environ.pop("RAG_LLM_MODE", None)
        os.environ.pop("RAG_LLM_PROVIDER", None)


def test_get_llm_provider_gemini_when_configured() -> None:
    """When RAG_LLM_MODE=external and RAG_LLM_PROVIDER=gemini and GEMINI_API_KEY set, return GeminiLLM."""
    os.environ["RAG_LLM_MODE"] = "external"
    os.environ["RAG_LLM_PROVIDER"] = "gemini"
    os.environ["GEMINI_API_KEY"] = "test-key-for-gemini-unit-test"
    try:
        config = RAGConfig.from_env()
        assert config.llm_mode == ModelMode.EXTERNAL
        assert config.external_provider == "gemini"
        provider = get_llm_provider(config=config)
        assert type(provider).__name__ == "GeminiLLM"
    finally:
        os.environ.pop("RAG_LLM_MODE", None)
        os.environ.pop("RAG_LLM_PROVIDER", None)
        os.environ.pop("GEMINI_API_KEY", None)


def test_get_llm_provider_gemini_raises_without_key() -> None:
    """When external provider is gemini but GEMINI_API_KEY missing, raise ValueError."""
    os.environ["RAG_LLM_MODE"] = "external"
    os.environ["RAG_LLM_PROVIDER"] = "gemini"
    os.environ.pop("GEMINI_API_KEY", None)
    try:
        config = RAGConfig.from_env()
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            get_llm_provider(config=config)
    finally:
        os.environ.pop("RAG_LLM_MODE", None)
        os.environ.pop("RAG_LLM_PROVIDER", None)


def test_llm_provider_type_includes_external() -> None:
    """LLMProviderType enum includes OPENAI, ANTHROPIC, GEMINI, OPENAI_COMPATIBLE."""
    assert hasattr(LLMProviderType, "OPENAI")
    assert hasattr(LLMProviderType, "ANTHROPIC")
    assert hasattr(LLMProviderType, "GEMINI")
    assert hasattr(LLMProviderType, "OPENAI_COMPATIBLE")
    assert LLMProviderType.OPENAI.value == "openai"
    assert LLMProviderType.ANTHROPIC.value == "anthropic"
    assert LLMProviderType.GEMINI.value == "gemini"
    assert LLMProviderType.OPENAI_COMPATIBLE.value == "openai_compatible"
