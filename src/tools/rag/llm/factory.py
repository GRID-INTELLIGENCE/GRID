"""Factory for creating LLM providers."""

from enum import StrEnum

from ..config import ModelMode, RAGConfig
from .base import BaseLLMProvider
from .ollama_cloud import OllamaCloudLLM
from .ollama_local import OllamaLocalLLM


class LLMProviderType(StrEnum):
    """Types of LLM providers."""

    OLLAMA_LOCAL = "ollama-local"  # Local Ollama models (default)
    OLLAMA_CLOUD = "ollama-cloud"  # Cloud Ollama models
    COPILOT = "copilot"  # GitHub Copilot SDK with web fetching
    OPENAI = "openai"  # OpenAI API (or OpenAI-compatible via base_url)
    ANTHROPIC = "anthropic"  # Anthropic Claude API
    GEMINI = "gemini"  # Google Gemini API
    OPENAI_COMPATIBLE = "openai_compatible"  # LiteLLM or any OpenAI-compatible endpoint
    SIMPLE = "simple"  # Simple fallback


def get_llm_provider(
    provider_type: str | None = None, config: RAGConfig | None = None, model: str | None = None
) -> BaseLLMProvider:
    """Get an LLM provider with local/cloud/external selection.

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
        elif config.llm_mode == ModelMode.EXTERNAL:
            provider_type = (config.external_provider or "openai").lower()
        else:
            provider_type = LLMProviderType.OLLAMA_LOCAL.value

    provider_type = provider_type.lower()

    # Determine model
    if model is None:
        if config.llm_mode == ModelMode.CLOUD:
            model = config.llm_model_cloud or "llama2"
        elif config.llm_mode == ModelMode.COPILOT:
            model = config.llm_model_copilot
        elif config.llm_mode == ModelMode.EXTERNAL:
            if provider_type == LLMProviderType.OPENAI.value:
                model = config.openai_model
            elif provider_type == LLMProviderType.ANTHROPIC.value:
                model = config.anthropic_model
            elif provider_type == LLMProviderType.GEMINI.value:
                model = config.gemini_model
            elif provider_type == LLMProviderType.OPENAI_COMPATIBLE.value:
                model = config.openai_model  # or a dedicated field; reuse openai_model
            else:
                model = config.openai_model
        else:
            model = config.llm_model_local

    if provider_type == LLMProviderType.OLLAMA_LOCAL.value:
        return OllamaLocalLLM(model=model, base_url=config.ollama_base_url)
    elif provider_type == LLMProviderType.OLLAMA_CLOUD.value:
        if not config.ollama_cloud_url:
            raise ValueError(
                "Cloud LLM mode requires OLLAMA_CLOUD_URL to be set. For local-only operation, use local mode."
            )
        return OllamaCloudLLM(model=model, cloud_url=config.ollama_cloud_url)
    elif provider_type == LLMProviderType.COPILOT.value:
        from .copilot import CopilotLLM

        return CopilotLLM(model=model)
    elif provider_type == LLMProviderType.OPENAI.value:
        from .openai_llm import OpenAILLM

        if not config.openai_api_key:
            raise ValueError(
                "External OpenAI mode requires OPENAI_API_KEY. Set RAG_LLM_MODE=external and RAG_LLM_PROVIDER=openai."
            )
        return OpenAILLM(
            model=model,
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
        )
    elif provider_type == LLMProviderType.ANTHROPIC.value:
        from .anthropic_llm import AnthropicLLM

        if not config.anthropic_api_key:
            raise ValueError(
                "External Anthropic mode requires ANTHROPIC_API_KEY. Set RAG_LLM_MODE=external and RAG_LLM_PROVIDER=anthropic."
            )
        return AnthropicLLM(
            model=model,
            api_key=config.anthropic_api_key,
        )
    elif provider_type == LLMProviderType.OPENAI_COMPATIBLE.value:
        from .openai_compatible import OpenAICompatibleLLM

        api_base = config.llm_api_base or config.openai_base_url
        if not api_base:
            raise ValueError(
                "OpenAI-compatible mode requires OPENAI_BASE_URL or RAG_LLM_API_BASE. Set RAG_LLM_MODE=external and RAG_LLM_PROVIDER=openai_compatible."
            )
        return OpenAICompatibleLLM(
            model=model,
            api_base=api_base,
            api_key=config.openai_api_key,
        )
    elif provider_type == LLMProviderType.GEMINI.value:
        from .gemini import GeminiLLM

        if not config.gemini_api_key:
            raise ValueError(
                "External Gemini mode requires GEMINI_API_KEY. Set RAG_LLM_MODE=external and RAG_LLM_PROVIDER=gemini."
            )
        return GeminiLLM(
            model=model,
            api_key=config.gemini_api_key,
        )
    elif provider_type == LLMProviderType.SIMPLE.value:
        from .simple import SimpleLLM

        return SimpleLLM()
    else:
        raise ValueError(
            f"Unknown LLM provider type: {provider_type}. Available: {', '.join([e.value for e in LLMProviderType])}"
        )
