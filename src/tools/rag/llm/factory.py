"""Factory for creating LLM providers.

Supports three resolution paths:
1. **Catalog-based auto-select** (opt-in, docs-aligned): When
   ``RAG_LLM_MODE=auto`` *and* ``RAG_LLM_AUTO_SELECT=catalog``, delegate to
   :func:`tools.rag.auto_selector.select` with the caller's ``task_type``.
   Honours UNPROVISIONED MODE and the docs-segmented catalog in
   ``config/ollama-model-catalog.json``.
2. **Fallback chain** (default auto): Load ``config/ollama-models.json``, probe
   providers in order, return the first healthy one. Activated when
   ``RAG_LLM_MODE=auto`` (without ``RAG_LLM_AUTO_SELECT=catalog``) or when
   ``ollama-models.json`` exists and no explicit mode is set.
3. **Legacy explicit mode**: ``RAG_LLM_MODE=local|cloud|external|copilot``
   picks a single provider directly from env vars (original behavior).
"""

import json
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


def _use_catalog_auto_select() -> bool:
    """Check whether to use the catalog-based auto-selector.

    Opt-in: requires ``RAG_LLM_MODE=auto`` *and*
    ``RAG_LLM_AUTO_SELECT=catalog``. Defaults off to preserve existing
    behaviour and passing tests.
    """
    if os.environ.get("RAG_LLM_MODE", "").lower() != "auto":
        return False
    return os.environ.get("RAG_LLM_AUTO_SELECT", "").lower() == "catalog"


def _provider_from_entry(entry: "ModelEntry") -> BaseLLMProvider:  # noqa: F821
    """Instantiate a ``BaseLLMProvider`` from a catalog :class:`ModelEntry`.

    Mapping:

    * ``source == "local"`` or ``"cloud-bridged"`` → :class:`OllamaLocalLLM`
      talking to the local daemon at ``OLLAMA_BASE_URL`` (the daemon handles
      any cloud offloading for ``:cloud``-suffixed models).
    * ``source == "cloud"`` → :class:`OllamaCloudLLM` talking to the upstream
      Ollama cloud URL. Requires network (blocked under UNPROVISIONED).
    * ``source == "simple"`` (synthetic fallback) →
      :class:`tools.rag.llm.simple.SimpleLLM`.
    """
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    if entry.source in ("local", "cloud-bridged"):
        return OllamaLocalLLM(model=entry.name, base_url=base_url)
    if entry.source == "cloud":
        cloud_url = os.environ.get("OLLAMA_CLOUD_URL", "https://ollama.com")
        _cloud_api_key = os.environ.get("OLLAMA_API_KEY") or None
        if not _cloud_api_key:
            logger.warning(
                "Cloud Ollama mode active but OLLAMA_API_KEY is not set — requests will be sent unauthenticated"
            )
        return OllamaCloudLLM(model=entry.name, cloud_url=cloud_url, api_key=_cloud_api_key)
    # Synthetic fallback from auto_selector (no catalog match)
    from .simple import SimpleLLM

    return SimpleLLM()


def _provider_from_resolved(resolved: "ResolvedProvider") -> BaseLLMProvider:  # noqa: F821
    """Instantiate a BaseLLMProvider from a ResolvedProvider."""
    from ..model_resolver import ResolvedProvider  # noqa: F811 — runtime import for type

    assert isinstance(resolved, ResolvedProvider)

    if resolved.type in ("ollama-local",):
        return OllamaLocalLLM(
            model=resolved.model,
            base_url=resolved.url or "http://localhost:11434",
            timeout=max(1, resolved.timeout_ms // 1000),
        )
    if resolved.type in ("ollama-cloud",):
        _cloud_api_key = os.environ.get("OLLAMA_API_KEY") or None
        if not _cloud_api_key:
            logger.warning(
                "Cloud Ollama mode active but OLLAMA_API_KEY is not set — requests will be sent unauthenticated"
            )
        return OllamaCloudLLM(
            model=resolved.model,
            cloud_url=resolved.url or "",
            timeout=max(1, resolved.timeout_ms // 1000),
            api_key=_cloud_api_key,
        )
    if resolved.type == "openai":
        from .openai import OpenAILLM

        api_key = os.environ.get(resolved.api_key_env or "OPENAI_API_KEY", "")
        return OpenAILLM(model=resolved.model, api_key=api_key, base_url=resolved.url)
    if resolved.type == "anthropic":
        from .anthropic import AnthropicLLM

        api_key = os.environ.get(resolved.api_key_env or "ANTHROPIC_API_KEY", "")
        return AnthropicLLM(model=resolved.model, api_key=api_key)
    if resolved.type == "simple":
        from .simple import SimpleLLM

        return SimpleLLM()

    msg = f"Unsupported resolved provider type: {resolved.type}"
    raise ValueError(msg)


def get_llm_provider(
    provider_type: str | None = None,
    config: RAGConfig | None = None,
    model: str | None = None,
    *,
    task_type: str | None = None,
    scope: str | None = None,
    attributes: dict | None = None,
    session_category: str | None = None,
) -> BaseLLMProvider:
    """Get an LLM provider with catalog / fallback-chain / legacy selection.

    Resolution order when ``provider_type`` and ``model`` are both ``None``:

    1. **Catalog auto-select** if ``RAG_LLM_MODE=auto`` and
       ``RAG_LLM_AUTO_SELECT=catalog``. Delegates to
       :func:`tools.rag.auto_selector.select` with ``task_type``/``scope``/
       ``attributes``/``session_category``.
    2. **Fallback chain** from ``config/ollama-models.json`` when
       ``RAG_LLM_MODE=auto`` (or unset and the file is present).
    3. **Legacy explicit mode** — the original single-provider path.

    Args:
        provider_type: Type of provider (default: based on config).
        config: RAG configuration (optional).
        model: Specific model name (overrides config).
        task_type: Task category hint for catalog auto-select.
        scope: ``"local"``, ``"cloud"``, or ``"auto"`` — catalog-only.
        attributes: Attribute hints for catalog auto-select.
        session_category: Session category hint for catalog auto-select.

    Returns:
        LLM provider instance.
    """
    # --- Catalog auto-select (opt-in) ---
    if provider_type is None and model is None and _use_catalog_auto_select():
        try:
            from ..auto_selector import TaskRequest, select

            request = TaskRequest(
                task_type=task_type or "chat",
                scope=scope or "auto",  # type: ignore[arg-type]
                attributes=attributes or {},
                session_category=session_category,
            )
            selection = select(request)
            logger.info(
                "llm_factory.catalog_auto_select model=%s reason=%s",
                selection.entry.name,
                selection.trace.reason,
            )
            return _provider_from_entry(selection.entry)
        except (
            ImportError,
            FileNotFoundError,
            OSError,
            json.JSONDecodeError,
            ValueError,
            KeyError,
        ) as exc:
            # B2 / N11: narrowed from `except Exception`. Expected failure modes of
            # the catalog auto-select path:
            #   - ImportError           — optional auto_selector module unavailable
            #   - FileNotFoundError     — ollama-model-catalog.json missing
            #   - OSError               — unreadable catalog / overrides file
            #   - json.JSONDecodeError  — malformed catalog / overrides JSON
            #                             (subclass of ValueError; named explicitly
            #                             for reader intent)
            #   - ValueError, KeyError  — dataclass parsing in model_catalog._parse_entry
            # Note: this path uses dataclasses (not Pydantic), so pydantic.ValidationError
            # is NOT part of the contract. Programmer errors (AttributeError, TypeError,
            # NameError) are intentionally allowed to surface rather than silently
            # fall through to path 2.
            logger.warning("llm_factory.catalog_auto_select failed, falling through to path 2: %s", exc)

    # --- Fallback chain path ---
    if provider_type is None and model is None and _use_fallback_chain():
        from ..model_resolver import resolve_llm

        resolved = resolve_llm()
        logger.info("llm_factory.fallback_chain provider=%s model=%s", resolved.label, resolved.model)
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
        if not config.ollama_api_key:
            logger.warning(
                "Cloud Ollama mode active but OLLAMA_API_KEY is not set — requests will be sent unauthenticated"
            )
        return OllamaCloudLLM(model=model, cloud_url=config.ollama_cloud_url, api_key=config.ollama_api_key)
    elif provider_type == LLMProviderType.COPILOT.value:
        from .copilot import CopilotLLM

        return CopilotLLM(model=model)
    elif provider_type == LLMProviderType.OPENAI.value:
        from .openai import OpenAILLM

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
        from .anthropic import AnthropicLLM

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
