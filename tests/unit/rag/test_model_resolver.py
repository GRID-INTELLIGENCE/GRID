"""Tests for tools.rag.model_resolver — functional API with provider fallback chains.

Coverage targets:
  - ResolvedProvider frozen dataclass
  - _find_config_path (env-var override, project root search, missing file)
  - load_model_config (valid JSON, malformed JSON, missing chains)
  - _probe_ollama (200/500/connection error)
  - _probe_provider (ollama types, API key check, simple provider)
  - Health cache: TTL expiration, success vs failure TTL, cache clearing
  - _resolve_chain (fallback, fixed, all-unhealthy, empty providers)
  - _to_resolved (defaults, label fallback, explicit values)
  - resolve_llm / resolve_embedding / clear_health_cache
  - ModelMode.AUTO value in config.py
  - LLM factory AUTO-mode branch and _provider_from_resolved
  - Embedding factory AUTO-mode branch and _embedding_from_resolved
  - Default config/ollama-models.json well-formed
  - Schema file config/schemas/ollama-models.schema.json valid
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Shared test fixture data
# ---------------------------------------------------------------------------

_MINIMAL_CONFIG: dict = {
    "llm": {
        "strategy": "fallback",
        "providers": [
            {
                "type": "ollama-cloud",
                "label": "cloud-llm",
                "model": "mistral:latest",
                "url": "https://api.ollama.com",
                "health_check": True,
                "health_timeout_ms": 3000,
                "timeout_ms": 30000,
            },
            {
                "type": "ollama-local",
                "label": "local-llm",
                "model": "ministral:latest",
                "url": "http://localhost:11434",
                "health_check": True,
                "health_timeout_ms": 2000,
                "timeout_ms": 120000,
            },
        ],
    },
    "embedding": {
        "strategy": "fallback",
        "providers": [
            {
                "type": "ollama-cloud",
                "label": "cloud-embed",
                "model": "nomic-embed-text-v2-moe:latest",
                "url": "https://api.ollama.com",
                "health_check": True,
                "health_timeout_ms": 3000,
                "timeout_ms": 15000,
            },
            {
                "type": "ollama-local",
                "label": "local-embed",
                "model": "nomic-embed-text-v2-moe:latest",
                "url": "http://localhost:11434",
                "health_check": True,
                "health_timeout_ms": 2000,
                "timeout_ms": 30000,
            },
        ],
    },
    "health": {
        "enabled": True,
        "cache_ttl_s": 60,
        "retry_backoff_s": 30,
    },
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    """Write _MINIMAL_CONFIG to a temp file and return its path."""
    p = tmp_path / "ollama-models.json"
    p.write_text(json.dumps(_MINIMAL_CONFIG), encoding="utf-8")
    return p


@pytest.fixture(autouse=True)
def _clear_health_cache():
    """Clear the module-level health cache before and after every test."""
    from tools.rag.model_resolver import clear_health_cache

    clear_health_cache()
    yield
    clear_health_cache()


# ===========================================================================
# ResolvedProvider
# ===========================================================================


class TestResolvedProvider:
    def test_fields_populated_correctly(self):
        from tools.rag.model_resolver import ResolvedProvider

        rp = ResolvedProvider(
            type="ollama-local",
            model="mistral:latest",
            url="http://localhost:11434",
            label="test-label",
        )
        assert rp.type == "ollama-local"
        assert rp.model == "mistral:latest"
        assert rp.url == "http://localhost:11434"
        assert rp.label == "test-label"
        assert rp.api_key_env is None
        assert rp.timeout_ms == 30000

    def test_frozen_raises_on_assignment(self):
        from tools.rag.model_resolver import ResolvedProvider

        rp = ResolvedProvider(type="ollama-local", model="m", label="x")
        with pytest.raises((AttributeError, TypeError)):
            rp.label = "other"  # type: ignore[misc]

    def test_optional_fields_accepted(self):
        from tools.rag.model_resolver import ResolvedProvider

        rp = ResolvedProvider(
            type="openai",
            model="gpt-4",
            url="https://api.openai.com",
            api_key_env="OPENAI_API_KEY",
            timeout_ms=90000,
            label="my-openai",
        )
        assert rp.api_key_env == "OPENAI_API_KEY"
        assert rp.timeout_ms == 90000

    def test_equality_by_value(self):
        from tools.rag.model_resolver import ResolvedProvider

        a = ResolvedProvider(type="ollama-local", model="m", label="x")
        b = ResolvedProvider(type="ollama-local", model="m", label="x")
        assert a == b

    def test_different_labels_are_not_equal(self):
        from tools.rag.model_resolver import ResolvedProvider

        a = ResolvedProvider(type="ollama-local", model="m", label="a")
        b = ResolvedProvider(type="ollama-local", model="m", label="b")
        assert a != b


# ===========================================================================
# Config discovery — _find_config_path
# ===========================================================================


class TestFindConfigPath:
    def test_env_var_points_to_existing_file(self, config_file: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("GRID_OLLAMA_MODELS_CONFIG", str(config_file))
        from tools.rag.model_resolver import _find_config_path

        assert _find_config_path() == config_file

    def test_env_var_missing_file_falls_through_to_search(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("GRID_OLLAMA_MODELS_CONFIG", str(tmp_path / "ghost.json"))
        from tools.rag.model_resolver import _find_config_path

        # Should still find the project-root config if it exists, or raise
        # We test the raises case when nothing exists anywhere
        monkeypatch.setattr("tools.rag.model_resolver.Path.__file__", str(tmp_path / "fake.py"), raising=False)
        # The function walks up from __file__ — if no config anywhere, raises
        try:
            result = _find_config_path()
            # If it found the real project config, that's fine
            assert result.is_file()
        except FileNotFoundError:
            pass  # Expected when config isn't in any ancestor

    def test_project_root_search_finds_config(self):
        """The real project config/ollama-models.json should be findable."""
        from tools.rag.model_resolver import _find_config_path

        # With no env var override, should find from project root
        result = _find_config_path()
        assert result.is_file()
        assert result.name == "ollama-models.json"

    def test_missing_config_raises_file_not_found(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("GRID_OLLAMA_MODELS_CONFIG", raising=False)
        # Patch Path.is_file to always return False so no config is found
        with patch("tools.rag.model_resolver.Path.is_file", return_value=False):
            from tools.rag.model_resolver import _find_config_path

            with pytest.raises(FileNotFoundError):
                _find_config_path()


# ===========================================================================
# Config loading — load_model_config
# ===========================================================================


class TestLoadModelConfig:
    def test_valid_config_loaded(self, config_file: Path):
        from tools.rag.model_resolver import load_model_config

        config = load_model_config(config_file)
        assert len(config.llm_providers) == 2
        assert config.llm_strategy == "fallback"
        assert len(config.embedding_providers) == 2
        assert config.embedding_strategy == "fallback"
        assert config.health.enabled is True
        assert config.health.cache_ttl_s == 60

    def test_malformed_json_raises(self, tmp_path: Path):
        bad = tmp_path / "ollama-models.json"
        bad.write_text("{not: valid json!!!", encoding="utf-8")
        from tools.rag.model_resolver import load_model_config

        with pytest.raises(json.JSONDecodeError):
            load_model_config(bad)

    def test_missing_chains_use_defaults(self, tmp_path: Path):
        minimal = tmp_path / "ollama-models.json"
        minimal.write_text("{}", encoding="utf-8")
        from tools.rag.model_resolver import load_model_config

        config = load_model_config(minimal)
        assert config.llm_providers == []
        assert config.embedding_providers == []
        assert config.llm_strategy == "fallback"
        assert config.health.enabled is True

    def test_health_config_defaults(self, tmp_path: Path):
        no_health = tmp_path / "ollama-models.json"
        no_health.write_text(json.dumps({"llm": {"providers": []}, "embedding": {"providers": []}}), encoding="utf-8")
        from tools.rag.model_resolver import load_model_config

        config = load_model_config(no_health)
        assert config.health.enabled is True
        assert config.health.cache_ttl_s == 60
        assert config.health.retry_backoff_s == 30


# ===========================================================================
# Health probing
# ===========================================================================


class TestProbeOllama:
    def test_returns_true_on_200(self):
        from tools.rag.model_resolver import _probe_ollama

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__.return_value.get.return_value = mock_resp
            assert _probe_ollama("http://localhost:11434", 2000) is True

    def test_returns_false_on_500(self):
        from tools.rag.model_resolver import _probe_ollama

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        with patch("httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__.return_value.get.return_value = mock_resp
            assert _probe_ollama("http://localhost:11434", 2000) is False

    def test_returns_false_on_connection_error(self):
        import httpx

        from tools.rag.model_resolver import _probe_ollama

        with patch("httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__.return_value.get.side_effect = httpx.ConnectError("refused")
            assert _probe_ollama("http://localhost:11434", 100) is False

    def test_returns_false_on_timeout(self):
        import httpx

        from tools.rag.model_resolver import _probe_ollama

        with patch("httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__.return_value.get.side_effect = httpx.TimeoutException("timeout")
            assert _probe_ollama("http://localhost:11434", 100) is False


class TestProbeProvider:
    def test_ollama_cloud_delegates_to_probe_ollama(self):
        from tools.rag.model_resolver import _probe_provider

        provider = {"type": "ollama-cloud", "url": "https://api.ollama.com", "health_timeout_ms": 2000}
        with patch("tools.rag.model_resolver._probe_ollama", return_value=True) as mock:
            assert _probe_provider(provider) is True
            mock.assert_called_once_with("https://api.ollama.com", 2000)

    def test_ollama_local_delegates_to_probe_ollama(self):
        from tools.rag.model_resolver import _probe_provider

        provider = {"type": "ollama-local", "url": "http://localhost:11434", "health_timeout_ms": 2000}
        with patch("tools.rag.model_resolver._probe_ollama", return_value=True):
            assert _probe_provider(provider) is True

    def test_openai_checks_api_key_env(self, monkeypatch: pytest.MonkeyPatch):
        from tools.rag.model_resolver import _probe_provider

        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        provider = {"type": "openai", "api_key_env": "OPENAI_API_KEY"}
        assert _probe_provider(provider) is True

    def test_openai_missing_key_returns_false(self, monkeypatch: pytest.MonkeyPatch):
        from tools.rag.model_resolver import _probe_provider

        monkeypatch.delenv("NONEXISTENT_KEY", raising=False)
        provider = {"type": "openai", "api_key_env": "NONEXISTENT_KEY"}
        assert _probe_provider(provider) is False

    def test_simple_always_healthy(self):
        from tools.rag.model_resolver import _probe_provider

        assert _probe_provider({"type": "simple"}) is True

    def test_unknown_type_returns_false(self):
        from tools.rag.model_resolver import _probe_provider

        assert _probe_provider({"type": "unknown-provider"}) is False


# ===========================================================================
# Health cache
# ===========================================================================


class TestHealthCache:
    def test_cache_hit_returns_cached_healthy(self, config_file: Path):
        from tools.rag.model_resolver import HealthConfig, _cache_key, _health_cache, _resolve_chain

        providers = _MINIMAL_CONFIG["llm"]["providers"]
        health = HealthConfig(enabled=True, cache_ttl_s=60, retry_backoff_s=30)

        # Pre-populate cache with healthy result
        key = _cache_key(providers[0], "llm")
        _health_cache[key] = (True, time.monotonic() + 60)

        with patch("tools.rag.model_resolver._probe_provider") as mock_probe:
            result = _resolve_chain(providers, "fallback", health, "llm")
            # Should not probe — cache hit
            mock_probe.assert_not_called()

        assert result.label == "cloud-llm"

    def test_cache_miss_triggers_probe(self, config_file: Path):
        from tools.rag.model_resolver import HealthConfig, _resolve_chain

        providers = _MINIMAL_CONFIG["llm"]["providers"]
        health = HealthConfig(enabled=True, cache_ttl_s=60, retry_backoff_s=30)

        with patch("tools.rag.model_resolver._probe_provider", return_value=True) as mock_probe:
            _resolve_chain(providers, "fallback", health, "llm")
            assert mock_probe.call_count >= 1

    def test_expired_cache_re_probes(self):
        from tools.rag.model_resolver import HealthConfig, _cache_key, _health_cache, _resolve_chain

        providers = _MINIMAL_CONFIG["llm"]["providers"]
        health = HealthConfig(enabled=True, cache_ttl_s=0, retry_backoff_s=0)

        # Pre-populate with expired entry
        key = _cache_key(providers[0], "llm")
        _health_cache[key] = (True, time.monotonic() - 1)

        with patch("tools.rag.model_resolver._probe_provider", return_value=True) as mock_probe:
            _resolve_chain(providers, "fallback", health, "llm")
            assert mock_probe.call_count >= 1

    def test_failure_uses_retry_backoff_ttl(self):
        from tools.rag.model_resolver import HealthConfig, _cache_key, _health_cache, _resolve_chain

        providers = [_MINIMAL_CONFIG["llm"]["providers"][0]]  # Single provider
        health = HealthConfig(enabled=True, cache_ttl_s=60, retry_backoff_s=10)

        with patch("tools.rag.model_resolver._probe_provider", return_value=False):
            _resolve_chain(providers, "fallback", health, "llm")

        key = _cache_key(providers[0], "llm")
        cached_healthy, expires = _health_cache[key]
        assert cached_healthy is False
        # Expiry should use retry_backoff_s (10), not cache_ttl_s (60)
        assert expires <= time.monotonic() + 11

    def test_clear_health_cache(self):
        from tools.rag.model_resolver import _health_cache, clear_health_cache

        _health_cache["test_key"] = (True, time.monotonic() + 60)
        assert len(_health_cache) >= 1
        clear_health_cache()
        assert len(_health_cache) == 0

    def test_health_check_false_skips_probe(self):
        from tools.rag.model_resolver import HealthConfig, _resolve_chain

        providers = [
            {
                "type": "ollama-local",
                "model": "m",
                "url": "http://localhost:11434",
                "health_check": False,
                "label": "no-check",
            },
        ]
        health = HealthConfig(enabled=True, cache_ttl_s=60, retry_backoff_s=30)

        with patch("tools.rag.model_resolver._probe_provider") as mock_probe:
            result = _resolve_chain(providers, "fallback", health, "llm")
            mock_probe.assert_not_called()

        assert result.label == "no-check"


# ===========================================================================
# Chain resolution — _resolve_chain
# ===========================================================================


class TestResolveChain:
    def test_fallback_selects_first_healthy(self):
        from tools.rag.model_resolver import HealthConfig, _resolve_chain

        providers = _MINIMAL_CONFIG["llm"]["providers"]
        health = HealthConfig(enabled=True, cache_ttl_s=60, retry_backoff_s=30)

        with patch("tools.rag.model_resolver._probe_provider", return_value=True):
            result = _resolve_chain(providers, "fallback", health, "llm")

        assert result.label == "cloud-llm"
        assert result.model == "mistral:latest"

    def test_fallback_skips_unhealthy_to_second(self):
        from tools.rag.model_resolver import HealthConfig, _resolve_chain

        providers = _MINIMAL_CONFIG["llm"]["providers"]
        health = HealthConfig(enabled=True, cache_ttl_s=60, retry_backoff_s=30)

        def probe_side(p):
            return p.get("type") == "ollama-local"

        with patch("tools.rag.model_resolver._probe_provider", side_effect=probe_side):
            result = _resolve_chain(providers, "fallback", health, "llm")

        assert result.label == "local-llm"

    def test_all_unhealthy_returns_last_as_fallback(self):
        from tools.rag.model_resolver import HealthConfig, _resolve_chain

        providers = _MINIMAL_CONFIG["llm"]["providers"]
        health = HealthConfig(enabled=True, cache_ttl_s=60, retry_backoff_s=30)

        with patch("tools.rag.model_resolver._probe_provider", return_value=False):
            result = _resolve_chain(providers, "fallback", health, "llm")

        assert result.label == "local-llm"

    def test_fixed_strategy_uses_first_without_probing(self, tmp_path: Path):
        from tools.rag.model_resolver import HealthConfig, _resolve_chain

        providers = [
            {"type": "ollama-local", "label": "only", "model": "qwen:7b", "url": "http://localhost:11434"},
        ]
        health = HealthConfig(enabled=True, cache_ttl_s=60, retry_backoff_s=30)

        with patch("tools.rag.model_resolver._probe_provider") as mock_probe:
            result = _resolve_chain(providers, "fixed", health, "llm")
            mock_probe.assert_not_called()

        assert result.label == "only"
        assert result.model == "qwen:7b"

    def test_health_disabled_uses_first_without_probing(self):
        from tools.rag.model_resolver import HealthConfig, _resolve_chain

        providers = _MINIMAL_CONFIG["llm"]["providers"]
        health = HealthConfig(enabled=False, cache_ttl_s=60, retry_backoff_s=30)

        with patch("tools.rag.model_resolver._probe_provider") as mock_probe:
            result = _resolve_chain(providers, "fallback", health, "llm")
            mock_probe.assert_not_called()

        assert result.label == "cloud-llm"

    def test_empty_providers_raises_value_error(self):
        from tools.rag.model_resolver import HealthConfig, _resolve_chain

        health = HealthConfig(enabled=True, cache_ttl_s=60, retry_backoff_s=30)
        with pytest.raises(ValueError, match="No providers configured"):
            _resolve_chain([], "fallback", health, "llm")

    def test_three_providers_skips_first_two_unhealthy(self):
        from tools.rag.model_resolver import HealthConfig, _resolve_chain

        providers = [
            {"type": "ollama-cloud", "label": "c1", "model": "m1", "url": "https://a.example.com"},
            {"type": "ollama-cloud", "label": "c2", "model": "m2", "url": "https://b.example.com"},
            {"type": "ollama-local", "label": "local", "model": "m3", "url": "http://localhost:11434"},
        ]
        health = HealthConfig(enabled=True, cache_ttl_s=60, retry_backoff_s=30)

        def probe(p):
            return "localhost" in p.get("url", "")

        with patch("tools.rag.model_resolver._probe_provider", side_effect=probe):
            result = _resolve_chain(providers, "fallback", health, "llm")

        assert result.label == "local"

    def test_single_provider_chain(self):
        from tools.rag.model_resolver import HealthConfig, _resolve_chain

        providers = [
            {"type": "ollama-local", "label": "solo", "model": "mistral:latest", "url": "http://localhost:11434"},
        ]
        health = HealthConfig(enabled=True, cache_ttl_s=60, retry_backoff_s=30)

        with patch("tools.rag.model_resolver._probe_provider", return_value=True):
            result = _resolve_chain(providers, "fallback", health, "llm")

        assert result.label == "solo"


# ===========================================================================
# _to_resolved helper
# ===========================================================================


class TestToResolved:
    def test_all_fields_mapped(self):
        from tools.rag.model_resolver import _to_resolved

        p = {
            "type": "openai",
            "model": "gpt-4",
            "url": "https://api.openai.com",
            "api_key_env": "OPENAI_API_KEY",
            "timeout_ms": 90000,
            "label": "my-openai",
        }
        rp = _to_resolved(p)
        assert rp.type == "openai"
        assert rp.model == "gpt-4"
        assert rp.url == "https://api.openai.com"
        assert rp.api_key_env == "OPENAI_API_KEY"
        assert rp.timeout_ms == 90000
        assert rp.label == "my-openai"

    def test_default_timeout(self):
        from tools.rag.model_resolver import _to_resolved

        rp = _to_resolved({"type": "ollama-local", "model": "llama2"})
        assert rp.timeout_ms == 30000

    def test_label_falls_back_to_type(self):
        from tools.rag.model_resolver import _to_resolved

        rp = _to_resolved({"type": "ollama-local", "model": "llama2"})
        assert rp.label == "ollama-local"

    def test_url_defaults_to_none(self):
        from tools.rag.model_resolver import _to_resolved

        rp = _to_resolved({"type": "simple", "model": "simple"})
        assert rp.url is None


# ===========================================================================
# Module-level resolve_llm / resolve_embedding / clear_health_cache
# ===========================================================================


class TestModuleLevelResolvers:
    def test_resolve_llm_with_config(self, config_file: Path):
        from tools.rag.model_resolver import load_model_config, resolve_llm

        config = load_model_config(config_file)
        with patch("tools.rag.model_resolver._probe_provider", return_value=True):
            result = resolve_llm(config)
        assert result.model == "mistral:latest"
        assert result.label == "cloud-llm"

    def test_resolve_embedding_with_config(self, config_file: Path):
        from tools.rag.model_resolver import load_model_config, resolve_embedding

        config = load_model_config(config_file)
        with patch("tools.rag.model_resolver._probe_provider", return_value=True):
            result = resolve_embedding(config)
        assert "nomic" in result.model
        assert result.label == "cloud-embed"

    def test_resolve_llm_without_config_loads_default(self):
        from tools.rag.model_resolver import resolve_llm

        with patch("tools.rag.model_resolver._probe_provider", return_value=True):
            result = resolve_llm()
        assert result is not None
        assert result.model  # Should have a model name

    def test_resolve_embedding_without_config_loads_default(self):
        from tools.rag.model_resolver import resolve_embedding

        with patch("tools.rag.model_resolver._probe_provider", return_value=True):
            result = resolve_embedding()
        assert result is not None


# ===========================================================================
# ModelMode.AUTO
# ===========================================================================


class TestModelModeAuto:
    def test_auto_value_is_string_auto(self):
        from tools.rag.config import ModelMode

        assert ModelMode.AUTO == "auto"
        assert ModelMode.AUTO.value == "auto"

    def test_auto_is_str_enum(self):
        from tools.rag.config import ModelMode

        assert isinstance(ModelMode.AUTO, str)

    def test_auto_parseable_from_string(self):
        from tools.rag.config import ModelMode

        assert ModelMode("auto") is ModelMode.AUTO

    def test_all_five_modes_present(self):
        from tools.rag.config import ModelMode

        expected = {"local", "cloud", "copilot", "external", "auto"}
        assert expected <= {m.value for m in ModelMode}

    def test_auto_not_equal_to_local(self):
        from tools.rag.config import ModelMode

        assert ModelMode.AUTO != ModelMode.LOCAL


# ===========================================================================
# LLM factory — _provider_from_resolved
# ===========================================================================


class TestLLMProviderFromResolved:
    def test_ollama_local_creates_provider(self):
        from tools.rag.llm.factory import _provider_from_resolved
        from tools.rag.llm.ollama_local import OllamaLocalLLM
        from tools.rag.model_resolver import ResolvedProvider

        rp = ResolvedProvider(type="ollama-local", model="llama2", url="http://localhost:11434", label="l")
        p = _provider_from_resolved(rp)
        assert isinstance(p, OllamaLocalLLM)
        assert p.model == "llama2"

    def test_ollama_cloud_creates_cloud_provider(self):
        from tools.rag.llm.factory import _provider_from_resolved
        from tools.rag.llm.ollama_cloud import OllamaCloudLLM
        from tools.rag.model_resolver import ResolvedProvider

        rp = ResolvedProvider(type="ollama-cloud", model="mistral:latest", url="https://api.ollama.com", label="c")
        p = _provider_from_resolved(rp)
        assert isinstance(p, OllamaCloudLLM)

    def test_openai_creates_provider(self, monkeypatch: pytest.MonkeyPatch):
        from tools.rag.llm.factory import _provider_from_resolved
        from tools.rag.model_resolver import ResolvedProvider

        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        rp = ResolvedProvider(
            type="openai", model="gpt-4", url="https://api.openai.com", api_key_env="OPENAI_API_KEY", label="oai"
        )
        p = _provider_from_resolved(rp)
        assert p is not None

    def test_simple_creates_provider(self):
        from tools.rag.llm.factory import _provider_from_resolved
        from tools.rag.model_resolver import ResolvedProvider

        rp = ResolvedProvider(type="simple", model="simple", label="s")
        p = _provider_from_resolved(rp)
        assert p is not None

    def test_unsupported_type_raises(self):
        from tools.rag.llm.factory import _provider_from_resolved
        from tools.rag.model_resolver import ResolvedProvider

        rp = ResolvedProvider(type="nonexistent", model="m", label="x")
        with pytest.raises(ValueError, match="Unsupported"):
            _provider_from_resolved(rp)

    def test_timeout_converted_from_ms_to_s(self):
        from tools.rag.llm.factory import _provider_from_resolved
        from tools.rag.llm.ollama_local import OllamaLocalLLM
        from tools.rag.model_resolver import ResolvedProvider

        rp = ResolvedProvider(type="ollama-local", model="m", url="http://localhost:11434", timeout_ms=60000, label="t")
        p = _provider_from_resolved(rp)
        assert isinstance(p, OllamaLocalLLM)
        assert p.timeout == 60


# ===========================================================================
# Embedding factory — _embedding_from_resolved
# ===========================================================================


class TestEmbeddingFromResolved:
    def test_ollama_local_creates_provider(self):
        from tools.rag.embeddings.factory import _embedding_from_resolved
        from tools.rag.embeddings.nomic_v2 import OllamaEmbeddingProvider
        from tools.rag.model_resolver import ResolvedProvider

        rp = ResolvedProvider(
            type="ollama-local", model="nomic-embed-text:latest", url="http://localhost:11434", label="e"
        )
        p = _embedding_from_resolved(rp)
        assert isinstance(p, OllamaEmbeddingProvider)

    def test_ollama_cloud_creates_provider_with_cloud_url(self):
        from tools.rag.embeddings.factory import _embedding_from_resolved
        from tools.rag.embeddings.nomic_v2 import OllamaEmbeddingProvider
        from tools.rag.model_resolver import ResolvedProvider

        rp = ResolvedProvider(
            type="ollama-cloud", model="nomic-embed-text-v2-moe:latest", url="https://api.ollama.com", label="ce"
        )
        p = _embedding_from_resolved(rp)
        assert isinstance(p, OllamaEmbeddingProvider)
        assert p.base_url == "https://api.ollama.com"

    def test_simple_creates_provider(self):
        from tools.rag.embeddings.factory import _embedding_from_resolved
        from tools.rag.model_resolver import ResolvedProvider

        rp = ResolvedProvider(type="simple", model="simple", label="s")
        p = _embedding_from_resolved(rp)
        assert p is not None

    def test_unsupported_type_raises(self):
        from tools.rag.embeddings.factory import _embedding_from_resolved
        from tools.rag.model_resolver import ResolvedProvider

        rp = ResolvedProvider(type="nonexistent", model="m", label="x")
        with pytest.raises(ValueError, match="Unsupported"):
            _embedding_from_resolved(rp)

    def test_explicit_simple_bypasses_auto(self):
        """Passing provider_type='simple' explicitly skips the AUTO chain."""
        from tools.rag.embeddings.factory import get_embedding_provider
        from tools.rag.embeddings.simple import SimpleEmbedding

        provider = get_embedding_provider(provider_type="simple")
        assert isinstance(provider, SimpleEmbedding)


# ===========================================================================
# LLM factory — AUTO mode integration
# ===========================================================================


class TestLLMFactoryAutoMode:
    def test_auto_mode_env_activates_chain(self, config_file: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("RAG_LLM_MODE", "auto")
        monkeypatch.setenv("GRID_OLLAMA_MODELS_CONFIG", str(config_file))

        from tools.rag.llm.factory import get_llm_provider

        with patch("tools.rag.model_resolver._probe_provider", return_value=True):
            provider = get_llm_provider()

        assert provider is not None

    def test_no_mode_with_config_activates_chain(self, config_file: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("RAG_LLM_MODE", raising=False)
        monkeypatch.setenv("GRID_OLLAMA_MODELS_CONFIG", str(config_file))

        from tools.rag.llm.factory import get_llm_provider

        with patch("tools.rag.model_resolver._probe_provider", return_value=True):
            provider = get_llm_provider()

        assert provider is not None

    def test_explicit_model_override_bypasses_chain(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("RAG_LLM_MODE", raising=False)
        from tools.rag.llm.factory import get_llm_provider
        from tools.rag.llm.ollama_local import OllamaLocalLLM

        # When model is explicitly passed, falls through to legacy path
        provider = get_llm_provider(model="custom:7b")
        assert isinstance(provider, OllamaLocalLLM)
        assert provider.model == "custom:7b"


# ===========================================================================
# Default config file (on disk)
# ===========================================================================


class TestDefaultConfigFile:
    """Verify the shipped config/ollama-models.json is present and well-formed."""

    @pytest.fixture()
    def default_config(self) -> dict:
        root = Path(__file__).resolve().parents[3]
        config_path = root / "config" / "ollama-models.json"
        assert config_path.exists(), f"ollama-models.json not found at {config_path}"
        return json.loads(config_path.read_text(encoding="utf-8"))

    def test_is_valid_json_object(self, default_config: dict):
        assert isinstance(default_config, dict)

    def test_top_level_keys_present(self, default_config: dict):
        assert "llm" in default_config
        assert "embedding" in default_config

    def test_health_section_present(self, default_config: dict):
        assert "health" in default_config
        h = default_config["health"]
        assert "enabled" in h
        assert "cache_ttl_s" in h
        assert "retry_backoff_s" in h

    def test_llm_chain_has_providers(self, default_config: dict):
        assert len(default_config["llm"]["providers"]) >= 1

    def test_embedding_chain_has_providers(self, default_config: dict):
        assert len(default_config["embedding"]["providers"]) >= 1

    def test_strategies_are_valid(self, default_config: dict):
        assert default_config["llm"].get("strategy", "fallback") in ("fallback", "fixed")
        assert default_config["embedding"].get("strategy", "fallback") in ("fallback", "fixed")

    def test_each_provider_has_required_fields(self, default_config: dict):
        for chain_key in ("llm", "embedding"):
            for p in default_config[chain_key]["providers"]:
                assert "type" in p, f"Provider in '{chain_key}' missing 'type'"
                assert "model" in p, f"Provider in '{chain_key}' missing 'model'"

    def test_cloud_providers_have_url(self, default_config: dict):
        for chain_key in ("llm", "embedding"):
            for p in default_config[chain_key]["providers"]:
                if "cloud" in p.get("type", ""):
                    assert "url" in p, f"Cloud provider in '{chain_key}' must have 'url'"

    def test_timeout_values_are_positive(self, default_config: dict):
        for chain_key in ("llm", "embedding"):
            for p in default_config[chain_key]["providers"]:
                if "timeout_ms" in p:
                    assert p["timeout_ms"] > 0
                if "health_timeout_ms" in p:
                    assert p["health_timeout_ms"] > 0

    def test_fallback_strategy_has_at_least_two_providers(self, default_config: dict):
        for chain_key in ("llm", "embedding"):
            chain = default_config[chain_key]
            if chain.get("strategy", "fallback") == "fallback":
                assert len(chain["providers"]) >= 2, f"Fallback chain '{chain_key}' should have >= 2 providers"


# ===========================================================================
# Schema file
# ===========================================================================


class TestSchemaFile:
    @pytest.fixture()
    def schema(self) -> dict:
        root = Path(__file__).resolve().parents[3]
        schema_path = root / "config" / "schemas" / "ollama-models.schema.json"
        assert schema_path.exists(), f"Schema not found at {schema_path}"
        return json.loads(schema_path.read_text(encoding="utf-8"))

    def test_is_valid_json_object(self, schema: dict):
        assert isinstance(schema, dict)

    def test_has_schema_version(self, schema: dict):
        assert "$schema" in schema

    def test_has_title(self, schema: dict):
        assert "title" in schema
        assert schema["title"]

    def test_requires_llm_and_embedding(self, schema: dict):
        required = schema.get("required", [])
        assert "llm" in required
        assert "embedding" in required

    def test_defs_block_present(self, schema: dict):
        defs = schema.get("$defs", {})
        assert "providerChain" in defs
        assert "provider" in defs
        assert "healthConfig" in defs

    def test_provider_chain_has_providers_property(self, schema: dict):
        chain = schema["$defs"]["providerChain"]
        assert "providers" in chain.get("properties", {})

    def test_provider_requires_type_and_model(self, schema: dict):
        provider = schema["$defs"]["provider"]
        required = provider.get("required", [])
        assert "type" in required
        assert "model" in required

    def test_strategy_enum_contains_fallback_and_fixed(self, schema: dict):
        strategy = schema["$defs"]["providerChain"]["properties"]["strategy"]
        assert set(strategy["enum"]) >= {"fallback", "fixed"}

    def test_provider_type_enum_contains_known_backends(self, schema: dict):
        type_prop = schema["$defs"]["provider"]["properties"]["type"]
        assert {"ollama-cloud", "ollama-local", "openai", "anthropic"} <= set(type_prop["enum"])

    def test_health_config_has_three_fields(self, schema: dict):
        props = schema["$defs"]["healthConfig"]["properties"]
        assert "enabled" in props
        assert "cache_ttl_s" in props
        assert "retry_backoff_s" in props

    def test_conditional_cloud_requires_url(self, schema: dict):
        """allOf must contain an if/then that requires url when type=ollama-cloud."""
        provider = schema["$defs"]["provider"]
        all_of = provider.get("allOf", [])
        assert len(all_of) >= 1, "Provider schema must have allOf conditionals"
        cloud_rule_found = any(
            rule.get("if", {}).get("properties", {}).get("type", {}).get("const") == "ollama-cloud"
            and "url" in rule.get("then", {}).get("required", [])
            for rule in all_of
        )
        assert cloud_rule_found, "Schema must require 'url' when type == 'ollama-cloud'"

    def test_conditional_openai_requires_api_key_env(self, schema: dict):
        provider = schema["$defs"]["provider"]
        all_of = provider.get("allOf", [])
        openai_rule_found = any(
            rule.get("if", {}).get("properties", {}).get("type", {}).get("const") == "openai"
            and "api_key_env" in rule.get("then", {}).get("required", [])
            for rule in all_of
        )
        assert openai_rule_found, "Schema must require 'api_key_env' when type == 'openai'"

    def test_conditional_anthropic_requires_api_key_env(self, schema: dict):
        provider = schema["$defs"]["provider"]
        all_of = provider.get("allOf", [])
        anthropic_rule_found = any(
            rule.get("if", {}).get("properties", {}).get("type", {}).get("const") == "anthropic"
            and "api_key_env" in rule.get("then", {}).get("required", [])
            for rule in all_of
        )
        assert anthropic_rule_found, "Schema must require 'api_key_env' when type == 'anthropic'"
