"""Factory for creating LLM providers.

Supports two resolution paths:
1. **Fallback chain** (default): Load config/ollama-models.json, probe providers
   in order, return the first healthy one. Activated when RAG_LLM_MODE=auto or
   when ollama-models.json exists and no explicit mode is set.
2. **Legacy explicit mode**: RAG_LLM_MODE=local|cloud|external|copilot picks a
   single provider directly from env vars (original behavior, still supported).
"""

import logging
import os
from enum import StrEnum

from ..config import ModelMode, RAGConfig
from .base import BaseLLMProvider
from .ollama_cloud import OllamaCloudLLM
from .ollama_local import OllamaLocalLLM

logger = logging.getLogger(__name__)


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


def _use_fallback_chain() -> bool:
    """Check whether to use the ollama-models.json fallback chain."""
    mode = os.environ.get("RAG_LLM_MODE", "").lower()
    if mode == "auto":
        return True
    # If no explicit mode, check if the config file exists
    if not mode:
        try:
            from ..model_resolver import _find_config_path

            _find_config_path()
            return True
        except FileNotFoundError:
            return False
    return False


def _provider_from_resolved(resolved: "ResolvedProvider") -> BaseLLMProvider:  # noqa: F821
    """Instantiate a BaseLLMProvider from a ResolvedProvider."""
    from ..model_resolver import ResolvedProvider  # noqa: F811 — runtime import for type

    assert isinstance(resolved, ResolvedProvider)

    if resolved.type in ("ollama-local",):
        return OllamaLocalLLM(
            model=resolved.model,
            base_url=resolved.url or "http://localhost:11434",
            timeout=resolved.timeout_ms // 1000,
        )
    if resolved.type in ("ollama-cloud",):
        return OllamaCloudLLM(
            model=resolved.model,
            cloud_url=resolved.url or "",
            timeout=resolved.timeout_ms // 1000,
        )
    if resolved.type == "openai":
        from .openai_llm import OpenAILLM

        api_key = os.environ.get(resolved.api_key_env or "OPENAI_API_KEY", "")
        return OpenAILLM(model=resolved.model, api_key=api_key, base_url=resolved.url)
    if resolved.type == "anthropic":
        from .anthropic_llm import AnthropicLLM

        api_key = os.environ.get(resolved.api_key_env or "ANTHROPIC_API_KEY", "")
        return AnthropicLLM(model=resolved.model, api_key=api_key)
    if resolved.type == "simple":
        from .simple import SimpleLLM

        return SimpleLLM()

    msg = f"Unsupported resolved provider type: {resolved.type}"
    raise ValueError(msg)


def get_llm_provider(
    provider_type: str | None = None, config: RAGConfig | None = None, model: str | None = None
) -> BaseLLMProvider:
    """Get an LLM provider with fallback-chain or legacy explicit selection.

    When RAG_LLM_MODE=auto (or unset with ollama-models.json present), uses the
    fallback chain from config/ollama-models.json — probing cloud first, falling
    back to local. Otherwise, falls through to the legacy single-provider path.

    Args:
        provider_type: Type of provider (default: based on config)
        config: RAG configuration (optional)
        model: Specific model name (overrides config)

    Returns:
        LLM provider instance
    """
    # --- Fallback chain path ---
    if provider_type is None and model is None and _use_fallback_chain():
        from ..model_resolver import resolve_llm

        resolved = resolve_llm()
        logger.info("llm_factory.fallback_chain", provider=resolved.label, model=resolved.model)
        return _provider_from_resolved(resolved)

    # --- Legacy explicit-mode path ---
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
