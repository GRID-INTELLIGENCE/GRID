"""Resolve LLM and embedding providers from ollama-models.json with fallback chains.

Loads config/ollama-models.json, probes provider health in order, and returns
the first healthy provider. Falls back through the chain automatically.
"""

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)

_CONFIG_PATH_ENV = "GRID_OLLAMA_MODELS_CONFIG"
_DEFAULT_CONFIG_REL = "config/ollama-models.json"

# Module-level health cache: {provider_key: (healthy: bool, expires_at: float)}
_health_cache: dict[str, tuple[bool, float]] = {}


@dataclass(frozen=True)
class ResolvedProvider:
    """A provider selected by the fallback resolver."""

    type: str
    model: str
    url: str | None = None
    api_key_env: str | None = None
    timeout_ms: int = 30000
    label: str = ""


@dataclass
class HealthConfig:
    """Global health-check settings."""

    enabled: bool = True
    cache_ttl_s: int = 60
    retry_backoff_s: int = 30


@dataclass
class ModelConfig:
    """Parsed ollama-models.json."""

    llm_providers: list[dict[str, Any]] = field(default_factory=list)
    llm_strategy: str = "fallback"
    embedding_providers: list[dict[str, Any]] = field(default_factory=list)
    embedding_strategy: str = "fallback"
    health: HealthConfig = field(default_factory=HealthConfig)


def _find_config_path() -> Path:
    """Locate ollama-models.json, checking env override then project root."""
    env_path = os.environ.get(_CONFIG_PATH_ENV)
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p

    # Walk up from this file to find the GRID project root (contains config/)
    here = Path(__file__).resolve().parent
    for ancestor in [here, *here.parents]:
        candidate = ancestor / _DEFAULT_CONFIG_REL
        if candidate.is_file():
            return candidate
        # Also check if we're in src/ and config/ is a sibling
        if (ancestor / "config" / "ollama-models.json").is_file():
            return ancestor / "config" / "ollama-models.json"

    msg = (
        f"ollama-models.json not found. Set {_CONFIG_PATH_ENV} or ensure "
        f"{_DEFAULT_CONFIG_REL} exists relative to the GRID project root."
    )
    raise FileNotFoundError(msg)


def load_model_config(path: Path | None = None) -> ModelConfig:
    """Load and parse ollama-models.json."""
    config_path = path or _find_config_path()
    with config_path.open() as f:
        raw = json.load(f)

    health_raw = raw.get("health", {})
    health = HealthConfig(
        enabled=health_raw.get("enabled", True),
        cache_ttl_s=health_raw.get("cache_ttl_s", 60),
        retry_backoff_s=health_raw.get("retry_backoff_s", 30),
    )

    llm = raw.get("llm", {})
    embedding = raw.get("embedding", {})

    return ModelConfig(
        llm_providers=llm.get("providers", []),
        llm_strategy=llm.get("strategy", "fallback"),
        embedding_providers=embedding.get("providers", []),
        embedding_strategy=embedding.get("strategy", "fallback"),
        health=health,
    )


def _cache_key(provider: dict[str, Any], chain: str) -> str:
    return f"{chain}:{provider.get('type')}:{provider.get('url', 'n/a')}:{provider.get('model')}"


def _probe_ollama(url: str, timeout_ms: int) -> bool:
    """Health-check an Ollama endpoint via GET /api/tags."""
    try:
        with httpx.Client(timeout=timeout_ms / 1000.0) as client:
            resp = client.get(f"{url.rstrip('/')}/api/tags")
            return resp.status_code == 200
    except (httpx.HTTPError, httpx.TimeoutException, OSError):
        return False


def _probe_provider(provider: dict[str, Any]) -> bool:
    """Run a health probe against a single provider."""
    ptype = provider.get("type", "")
    url = provider.get("url", "")
    health_timeout = provider.get("health_timeout_ms", 2000)

    if ptype in ("ollama-cloud", "ollama-local"):
        return _probe_ollama(url, health_timeout)
    if ptype in ("openai", "anthropic", "mistral", "openai-compatible"):
        # For API providers, check that the key env var is set
        key_env = provider.get("api_key_env", "")
        return bool(os.environ.get(key_env))
    if ptype == "simple":
        return True

    return False


def _resolve_chain(
    providers: list[dict[str, Any]],
    strategy: str,
    health: HealthConfig,
    chain_name: str,
) -> ResolvedProvider:
    """Walk the provider list and return the first healthy one."""
    if not providers:
        msg = f"No providers configured for {chain_name}"
        raise ValueError(msg)

    if strategy == "fixed" or not health.enabled:
        p = providers[0]
        logger.info("model_resolver.fixed", chain=chain_name, provider=p.get("label", p.get("type")))
        return _to_resolved(p)

    now = time.monotonic()

    for p in providers:
        key = _cache_key(p, chain_name)
        label = p.get("label", p.get("type"))

        # Check cache
        if key in _health_cache:
            cached_healthy, expires = _health_cache[key]
            if now < expires:
                if cached_healthy:
                    logger.debug("model_resolver.cache_hit", chain=chain_name, provider=label, healthy=True)
                    return _to_resolved(p)
                logger.debug("model_resolver.cache_hit", chain=chain_name, provider=label, healthy=False)
                continue

        # Skip health check if provider opts out
        if not p.get("health_check", True):
            logger.info("model_resolver.skip_probe", chain=chain_name, provider=label)
            _health_cache[key] = (True, now + health.cache_ttl_s)
            return _to_resolved(p)

        # Probe
        healthy = _probe_provider(p)
        ttl = health.cache_ttl_s if healthy else health.retry_backoff_s
        _health_cache[key] = (healthy, now + ttl)

        if healthy:
            logger.info("model_resolver.selected", chain=chain_name, provider=label, model=p.get("model"))
            return _to_resolved(p)

        logger.warning("model_resolver.unhealthy", chain=chain_name, provider=label)

    # All providers failed — return last as best-effort with a warning
    last = providers[-1]
    logger.error(
        "model_resolver.all_unhealthy",
        chain=chain_name,
        falling_back_to=last.get("label", last.get("type")),
    )
    return _to_resolved(last)


def _to_resolved(p: dict[str, Any]) -> ResolvedProvider:
    return ResolvedProvider(
        type=p["type"],
        model=p["model"],
        url=p.get("url"),
        api_key_env=p.get("api_key_env"),
        timeout_ms=p.get("timeout_ms", 30000),
        label=p.get("label", p.get("type", "")),
    )


def resolve_llm(config: ModelConfig | None = None) -> ResolvedProvider:
    """Resolve the LLM provider from the fallback chain."""
    if config is None:
        config = load_model_config()
    return _resolve_chain(config.llm_providers, config.llm_strategy, config.health, "llm")


def resolve_embedding(config: ModelConfig | None = None) -> ResolvedProvider:
    """Resolve the embedding provider from the fallback chain."""
    if config is None:
        config = load_model_config()
    return _resolve_chain(config.embedding_providers, config.embedding_strategy, config.health, "embedding")


def clear_health_cache() -> None:
    """Clear the health probe cache (useful for tests and manual refresh)."""
    _health_cache.clear()
