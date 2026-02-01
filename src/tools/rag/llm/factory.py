"""Factory for creating LLM providers."""

from enum import Enum

from ..config import ModelMode, RAGConfig
from .base import BaseLLMProvider
from .ollama_cloud import OllamaCloudLLM
from .ollama_local import OllamaLocalLLM


class LLMProviderType(str, Enum):
    """Types of LLM providers."""

    OLLAMA_LOCAL = "ollama-local"  # Local Ollama models (default)
    OLLAMA_CLOUD = "ollama-cloud"  # Cloud Ollama models
    COPILOT = "copilot"  # GitHub Copilot SDK with web fetching
    SIMPLE = "simple"  # Simple fallback


def get_llm_provider(
    provider_type: str | None = None, config: RAGConfig | None = None, model: str | None = None
) -> BaseLLMProvider:
    """Get an LLM provider with local/cloud selection.

    Args:
        provider_type: Type of provider (default: based on config)
        config: RAG configuration (optional)
        model: Specific model name (overrides config)

    Returns:
        LLM provider instance
    """
    if config is None:
        config = RAGConfig.from_env()

    # Determine provider type from config if not specified
    if provider_type is None:
        if config.llm_mode == ModelMode.CLOUD:
            provider_type = LLMProviderType.OLLAMA_CLOUD.value
        elif config.llm_mode == ModelMode.COPILOT:
            provider_type = LLMProviderType.COPILOT.value
        else:
            provider_type = LLMProviderType.OLLAMA_LOCAL.value

    provider_type = provider_type.lower()

    # Determine model
    if model is None:
        if config.llm_mode == ModelMode.CLOUD:
            model = config.llm_model_cloud or "llama2"
        elif config.llm_mode == ModelMode.COPILOT:
            model = config.llm_model_copilot
        else:
            model = config.llm_model_local

    if provider_type == LLMProviderType.OLLAMA_LOCAL.value:
        return OllamaLocalLLM(model=model, base_url=config.ollama_base_url)
    elif provider_type == LLMProviderType.OLLAMA_CLOUD.value:
        if not config.ollama_cloud_url:
            raise ValueError(
                "Cloud LLM mode requires OLLAMA_CLOUD_URL to be set. " "For local-only operation, use local mode."
            )
        return OllamaCloudLLM(model=model, cloud_url=config.ollama_cloud_url)
    elif provider_type == LLMProviderType.COPILOT.value:
        from .copilot import CopilotLLM
        return CopilotLLM(model=model)
    elif provider_type == LLMProviderType.SIMPLE.value:
        from .simple import SimpleLLM

        return SimpleLLM()
    else:
        raise ValueError(
            f"Unknown LLM provider type: {provider_type}. "
            f"Available: {', '.join([e.value for e in LLMProviderType])}"
        )
