"""Tests for the RAG resilience layer (tools.rag.resilience).

Validates:
  - Singleton behaviour of circuit breakers / token buckets
  - No-op fallback when apiguard is unavailable
  - Factory helpers return expected types
  - guarded_call / async_guarded_call propagate results and errors
"""

from __future__ import annotations

import importlib
import sys
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reload_resilience():
    """Force-reload resilience module so import-time logic re-runs."""
    mod_name = "tools.rag.resilience"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    return importlib.import_module(mod_name)


# ---------------------------------------------------------------------------
# Tests that always pass (work with or without apiguard)
# ---------------------------------------------------------------------------


class TestResilienceImport:
    """Module must import without error regardless of apiguard presence."""

    def test_import_succeeds(self):
        mod = _reload_resilience()
        assert hasattr(mod, "get_circuit_breaker")
        assert hasattr(mod, "get_token_bucket")
        assert hasattr(mod, "get_retry_handler")
        assert hasattr(mod, "create_async_resilient_client")
        assert hasattr(mod, "guarded_call")
        assert hasattr(mod, "async_guarded_call")


class TestNoOpFallback:
    """When apiguard is absent, every factory must return a usable no-op."""

    def test_noop_breaker_context_manager(self):
        mod = _reload_resilience()
        breaker = mod._NoOpBreaker()
        with breaker:
            pass  # must not raise

    def test_noop_breaker_api(self):
        mod = _reload_resilience()
        b = mod._NoOpBreaker()
        assert b.is_closed() is True
        assert b.is_open() is False
        b.reset()  # no-op, must not raise

    def test_get_circuit_breaker_returns_noop_when_unavailable(self):
        """Simulate apiguard missing by patching _APIGUARD_AVAILABLE."""
        mod = _reload_resilience()
        with patch.object(mod, "_APIGUARD_AVAILABLE", False):
            breaker = mod.get_circuit_breaker("test_service")
            assert isinstance(breaker, mod._NoOpBreaker)

    def test_get_token_bucket_returns_none_when_unavailable(self):
        mod = _reload_resilience()
        with patch.object(mod, "_APIGUARD_AVAILABLE", False):
            assert mod.get_token_bucket("test_service") is None

    def test_get_retry_handler_returns_none_when_unavailable(self):
        mod = _reload_resilience()
        with patch.object(mod, "_APIGUARD_AVAILABLE", False):
            assert mod.get_retry_handler("test_service") is None


class TestGuardedCalls:
    """guarded_call and async_guarded_call propagate correctly."""

    def test_guarded_call_returns_value(self):
        mod = _reload_resilience()
        result = mod.guarded_call("ollama", lambda x: x * 2, 21)
        assert result == 42

    def test_guarded_call_propagates_exception(self):
        mod = _reload_resilience()

        def boom():
            raise ValueError("test")

        with pytest.raises(ValueError, match="test"):
            mod.guarded_call("ollama", boom)

    @pytest.mark.asyncio
    async def test_async_guarded_call_returns_value(self):
        mod = _reload_resilience()

        async def double(x):
            return x * 2

        result = await mod.async_guarded_call("ollama", double, 21)
        assert result == 42

    @pytest.mark.asyncio
    async def test_async_guarded_call_propagates_exception(self):
        mod = _reload_resilience()

        async def boom():
            raise ValueError("async test")

        with pytest.raises(ValueError, match="async test"):
            await mod.async_guarded_call("ollama", boom)


# ---------------------------------------------------------------------------
# Tests that require apiguard
# ---------------------------------------------------------------------------

_has_apiguard = importlib.util.find_spec("apiguard") is not None  # type: ignore[union-attr]


@pytest.mark.skipif(not _has_apiguard, reason="apiguard not installed")
class TestWithAPIGuard:
    """Tests that validate real apiguard integration."""

    def test_circuit_breaker_singleton(self):
        mod = _reload_resilience()
        b1 = mod.get_circuit_breaker("ollama")
        b2 = mod.get_circuit_breaker("ollama")
        assert b1 is b2, "Same service must return the same breaker instance"

    def test_different_services_different_breakers(self):
        mod = _reload_resilience()
        b_ollama = mod.get_circuit_breaker("ollama")
        b_openai = mod.get_circuit_breaker("openai")
        assert b_ollama is not b_openai

    def test_token_bucket_singleton(self):
        mod = _reload_resilience()
        t1 = mod.get_token_bucket("openai")
        t2 = mod.get_token_bucket("openai")
        assert t1 is t2

    def test_retry_handler_is_fresh_each_call(self):
        mod = _reload_resilience()
        r1 = mod.get_retry_handler("openai")
        r2 = mod.get_retry_handler("openai")
        assert r1 is not r2, "Retry handlers are per-request, not singletons"

    def test_create_async_resilient_client_type(self):
        mod = _reload_resilience()
        from apiguard.adapters.httpx import AsyncRateLimitedClient

        client = mod.create_async_resilient_client("ollama")
        assert isinstance(client, AsyncRateLimitedClient)

    def test_unknown_service_uses_defaults(self):
        mod = _reload_resilience()
        breaker = mod.get_circuit_breaker("unknown_service_xyz")
        # Should use default (5, 60.0, 1) — just verify it exists
        assert breaker is not None
        assert breaker.is_closed()
