"""Regression tests for Phantom Wrapper Audit fixes.

Validates that external provider integrations no longer silently mask
failures with mock/fallback responses. Each test verifies that the
correct exception is raised instead of a silent degradation.

Covers:
- P1: StripeService, GeminiStudioClient, RAG embedding/LLM providers
- P2: Test provider namespace separation, ensure_local_only() enforcement
- P3: OnDemandRAGEngine degradation metadata
"""

# Load modules that are shadowed on sys.path via importlib.
import importlib.util as _ilu
import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest

_repo_root = Path(__file__).resolve().parent.parent


def _load_module(name: str, file_path: str):
    """Load a Python module from an absolute file path."""
    spec = _ilu.spec_from_file_location(name, file_path)
    if not spec or not spec.loader:
        return None
    mod = _ilu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# Gemini client: infrastructure/cloud/gemini_client.py (shadowed by src/infrastructure/)
_gemini_mod = _load_module(
    "_gemini_client_standalone",
    str(_repo_root / "infrastructure" / "cloud" / "gemini_client.py"),
)


# ---------------------------------------------------------------------------
# P1-1: StripeService — raises instead of silent mock
# ---------------------------------------------------------------------------


class TestStripeServicePhantomWrapper:
    """StripeService must return explicit result objects instead of magic strings or None."""

    @pytest.fixture
    def _mock_runtime_settings(self):
        """Create a mock RuntimeSettings with stripe disabled."""

        @dataclass
        class _Payment:
            stripe_secret_key: str = ""
            stripe_enabled: bool = False

        @dataclass
        class _Settings:
            payment: _Payment

            @classmethod
            def from_env(cls):
                return cls(payment=_Payment())

        return _Settings

    @pytest.fixture
    def _mock_runtime_settings_mock_mode(self):
        """Create a mock RuntimeSettings with stripe enabled but no key (mock mode)."""

        @dataclass
        class _Payment:
            stripe_secret_key: str = ""
            stripe_enabled: bool = True

        @dataclass
        class _Settings:
            payment: _Payment

            @classmethod
            def from_env(cls):
                return cls(payment=_Payment())

        return _Settings

    def test_disabled_stripe_returns_explicit_result_not_mock_id(self, _mock_runtime_settings):
        """When Stripe is intentionally disabled, service uses 'disabled' origin."""
        from grid.billing.stripe_service import StripeService

        with patch("grid.billing.stripe_service.RuntimeSettings", _mock_runtime_settings):
            with patch("grid.billing.stripe_service._is_production_environment", return_value=False):
                svc = StripeService()
                assert svc.enabled is False
                assert svc.origin == "disabled"

    @pytest.mark.asyncio
    async def test_disabled_stripe_create_customer_returns_result(self, _mock_runtime_settings):
        """Disabled Stripe returns CustomerResult with origin='disabled', not None."""
        from grid.billing.stripe_service import CustomerResult, StripeService

        with patch("grid.billing.stripe_service.RuntimeSettings", _mock_runtime_settings):
            with patch("grid.billing.stripe_service._is_production_environment", return_value=False):
                svc = StripeService()
                result = await svc.create_customer("user1", "user@example.com")
                assert isinstance(result, CustomerResult)
                assert result.id is None
                assert result.origin == "disabled"
                assert result.degraded is False

    @pytest.mark.asyncio
    async def test_disabled_stripe_create_subscription_returns_result(self, _mock_runtime_settings):
        """Disabled Stripe returns SubscriptionResult with origin='disabled', not None."""
        from grid.billing.stripe_service import StripeService, SubscriptionResult

        with patch("grid.billing.stripe_service.RuntimeSettings", _mock_runtime_settings):
            with patch("grid.billing.stripe_service._is_production_environment", return_value=False):
                svc = StripeService()
                result = await svc.create_subscription("cus_xxx", "price_xxx")
                assert isinstance(result, SubscriptionResult)
                assert result.subscription_id is None
                assert result.origin == "disabled"
                assert result.degraded is False

    @pytest.mark.asyncio
    async def test_disabled_stripe_report_usage_returns_result(self, _mock_runtime_settings):
        """Disabled Stripe returns UsageReportResult with origin='disabled'."""
        from grid.billing.stripe_service import StripeService, UsageReportResult

        with patch("grid.billing.stripe_service.RuntimeSettings", _mock_runtime_settings):
            with patch("grid.billing.stripe_service._is_production_environment", return_value=False):
                svc = StripeService()
                result = await svc.report_usage("si_xxx", 100)
                assert isinstance(result, UsageReportResult)
                assert result.success is False
                assert result.origin == "disabled"
                assert result.degraded is False

    def test_mock_mode_flag_set_when_enabled_without_key(self, _mock_runtime_settings_mock_mode):
        """When Stripe is enabled but no key is provided, origin is 'mock'."""
        from grid.billing.stripe_service import StripeService

        with patch("grid.billing.stripe_service.RuntimeSettings", _mock_runtime_settings_mock_mode):
            with patch("grid.billing.stripe_service._is_production_environment", return_value=False):
                svc = StripeService()
                assert svc.origin == "mock"
                assert svc.enabled is False

    @pytest.mark.asyncio
    async def test_mock_mode_returns_degraded_result(self, _mock_runtime_settings_mock_mode):
        """Mock mode returns degraded CustomerResult instead of raising."""
        from grid.billing.stripe_service import CustomerResult, StripeService

        with patch("grid.billing.stripe_service.RuntimeSettings", _mock_runtime_settings_mock_mode):
            with patch("grid.billing.stripe_service._is_production_environment", return_value=False):
                svc = StripeService()
                result = await svc.create_customer("user1", "user@example.com")
                assert isinstance(result, CustomerResult)
                assert result.origin == "mock"
                assert result.degraded is True
                assert result.is_simulated is True
                assert result.error is not None

    @pytest.mark.asyncio
    async def test_mock_mode_subscription_returns_degraded(self, _mock_runtime_settings_mock_mode):
        """Mock mode returns degraded SubscriptionResult instead of raising."""
        from grid.billing.stripe_service import StripeService, SubscriptionResult

        with patch("grid.billing.stripe_service.RuntimeSettings", _mock_runtime_settings_mock_mode):
            with patch("grid.billing.stripe_service._is_production_environment", return_value=False):
                svc = StripeService()
                result = await svc.create_subscription("cus_xxx", "price_xxx")
                assert isinstance(result, SubscriptionResult)
                assert result.origin == "mock"
                assert result.degraded is True
                assert result.is_simulated is True

    @pytest.mark.asyncio
    async def test_mock_mode_usage_returns_degraded(self, _mock_runtime_settings_mock_mode):
        """Mock mode returns degraded UsageReportResult instead of raising."""
        from grid.billing.stripe_service import StripeService, UsageReportResult

        with patch("grid.billing.stripe_service.RuntimeSettings", _mock_runtime_settings_mock_mode):
            with patch("grid.billing.stripe_service._is_production_environment", return_value=False):
                svc = StripeService()
                result = await svc.report_usage("si_xxx", 100)
                assert isinstance(result, UsageReportResult)
                assert result.origin == "mock"
                assert result.degraded is True
                assert result.is_simulated is True

    def test_production_guard_raises_when_disabled_in_prod(self, _mock_runtime_settings):
        """StripeService raises RuntimeError in production when disabled without override."""
        from grid.billing.stripe_service import StripeService

        with patch("grid.billing.stripe_service.RuntimeSettings", _mock_runtime_settings):
            with patch("grid.billing.stripe_service._is_production_environment", return_value=True):
                with pytest.raises(RuntimeError, match="not properly configured for production"):
                    StripeService()


# ---------------------------------------------------------------------------
# P1-2: GeminiStudioClient — raises GeminiAuthError instead of dry-run
# ---------------------------------------------------------------------------


@pytest.mark.skipif(_gemini_mod is None, reason="gemini_client.py not loadable")
class TestGeminiClientPhantomWrapper:
    """GeminiStudioClient must raise GeminiAuthError instead of returning dry-run text."""

    @pytest.fixture(autouse=True)
    def _patch_env(self):
        """Ensure non-production environment for all tests in this class."""
        original = _gemini_mod._is_production_environment
        _gemini_mod._is_production_environment = lambda: False
        yield
        _gemini_mod._is_production_environment = original

    def test_dry_run_detected_without_api_key(self):
        """Client sets _dry_run=True when no API key is provided."""
        config = _gemini_mod.GeminiConfig(api_key="")
        client = _gemini_mod.GeminiStudioClient(config=config)
        assert client._dry_run is True

    @pytest.mark.asyncio
    async def test_generate_raises_auth_error_in_dry_run(self):
        """generate() raises GeminiAuthError instead of returning '[DRY RUN]' text."""
        config = _gemini_mod.GeminiConfig(api_key="")
        client = _gemini_mod.GeminiStudioClient(config=config)
        with pytest.raises(_gemini_mod.GeminiAuthError, match="API key not configured"):
            await client.generate("test prompt")

    @pytest.mark.asyncio
    async def test_chat_raises_auth_error_in_dry_run(self):
        """chat() raises GeminiAuthError instead of returning dry-run GenerationResult."""
        config = _gemini_mod.GeminiConfig(api_key="")
        client = _gemini_mod.GeminiStudioClient(config=config)
        with pytest.raises(_gemini_mod.GeminiAuthError, match="API key not configured"):
            await client.chat([{"role": "user", "content": "hello"}])

    @pytest.mark.asyncio
    async def test_stream_raises_auth_error_in_dry_run(self):
        """stream() raises GeminiAuthError instead of yielding '[DRY RUN]' text."""
        config = _gemini_mod.GeminiConfig(api_key="")
        client = _gemini_mod.GeminiStudioClient(config=config)
        with pytest.raises(_gemini_mod.GeminiAuthError, match="API key not configured"):
            async for _ in client.stream("test prompt"):
                pass

    def test_production_guard_raises_without_key(self):
        """GeminiStudioClient raises RuntimeError in production without API key."""
        _gemini_mod._is_production_environment = lambda: True
        try:
            with pytest.raises(RuntimeError, match="forbidden in production"):
                config = _gemini_mod.GeminiConfig(api_key="")
                _gemini_mod.GeminiStudioClient(config=config)
        finally:
            _gemini_mod._is_production_environment = lambda: False

    def test_no_dry_run_with_api_key(self):
        """Client does NOT set _dry_run when API key is provided."""
        config = _gemini_mod.GeminiConfig(api_key="test-key-12345")
        client = _gemini_mod.GeminiStudioClient(config=config)
        assert client._dry_run is False


# ---------------------------------------------------------------------------
# P1-3: RAG Providers — raise instead of silent fallback
# ---------------------------------------------------------------------------


class TestRAGProviderErrorTypes:
    """Verify custom exception types exist and are usable."""

    def test_embedding_provider_error_exists(self):
        """EmbeddingProviderError is importable and is a RuntimeError."""
        from tools.rag.types import EmbeddingProviderError

        assert issubclass(EmbeddingProviderError, RuntimeError)
        err = EmbeddingProviderError("test error")
        assert str(err) == "test error"

    def test_llm_provider_error_exists(self):
        """LLMProviderError is importable and is a RuntimeError."""
        from tools.rag.types import LLMProviderError

        assert issubclass(LLMProviderError, RuntimeError)
        err = LLMProviderError("test error")
        assert str(err) == "test error"


class TestRAGLLMFactoryValidation:
    """LLM factory must raise ValueError for external providers missing API keys."""

    def test_openai_llm_factory_raises_without_key(self):
        """get_llm_provider raises ValueError when OpenAI API key is missing."""
        from tools.rag.config import ModelMode, RAGConfig
        from tools.rag.llm.factory import get_llm_provider

        config = RAGConfig(llm_mode=ModelMode.EXTERNAL, external_provider="openai", openai_api_key=None)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            get_llm_provider(config=config)

    def test_gemini_llm_factory_raises_without_key(self):
        """get_llm_provider raises ValueError when Gemini API key is missing."""
        from tools.rag.config import ModelMode, RAGConfig
        from tools.rag.llm.factory import get_llm_provider

        config = RAGConfig(llm_mode=ModelMode.EXTERNAL, external_provider="gemini", gemini_api_key=None)
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            get_llm_provider(config=config)

    def test_anthropic_llm_factory_raises_without_key(self):
        """get_llm_provider raises ValueError when Anthropic API key is missing."""
        from tools.rag.config import ModelMode, RAGConfig
        from tools.rag.llm.factory import get_llm_provider

        config = RAGConfig(llm_mode=ModelMode.EXTERNAL, external_provider="anthropic", anthropic_api_key=None)
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            get_llm_provider(config=config)


# ---------------------------------------------------------------------------
# P2-1: Test Provider — namespace separation
# ---------------------------------------------------------------------------


class TestTestProviderNamespaceSeparation:
    """TestEmbeddingProvider must not be importable from the public package API."""

    def test_test_provider_not_in_package_all(self):
        """TestEmbeddingProvider and get_test_provider are NOT in __all__."""
        from tools.rag.embeddings import __all__ as embedding_exports

        assert "TestEmbeddingProvider" not in embedding_exports
        assert "get_test_provider" not in embedding_exports

    def test_factory_rejects_test_provider_type(self):
        """get_embedding_provider() raises ValueError for provider_type='test'."""
        from tools.rag.embeddings.factory import get_embedding_provider

        with pytest.raises(ValueError, match="Test embedding provider cannot be used"):
            get_embedding_provider(provider_type="test")

    def test_test_provider_still_importable_directly(self):
        """Test provider is still importable directly for test code."""
        from tools.rag.embeddings.test_provider import (
            DeterministicEmbeddingProvider,
            get_test_provider,
        )

        provider = get_test_provider(singleton=False)
        assert isinstance(provider, DeterministicEmbeddingProvider)
        emb = provider.embed("hello")
        assert len(emb) == 384


# ---------------------------------------------------------------------------
# P2-2: RAG Config — ensure_local_only() enforcement
# ---------------------------------------------------------------------------


class TestEnsureLocalOnlyEnforcement:
    """ensure_local_only() must raise ValueError for external provider configs."""

    def test_raises_on_external_llm_mode(self):
        """ensure_local_only() raises when llm_mode is EXTERNAL."""
        from tools.rag.config import ModelMode, RAGConfig

        config = RAGConfig(llm_mode=ModelMode.EXTERNAL)
        with pytest.raises(ValueError, match="Local-only mode required"):
            config.ensure_local_only()

    def test_raises_on_external_embedding_provider(self):
        """ensure_local_only() raises when embedding_provider is 'openai'."""
        from tools.rag.config import ModelMode, RAGConfig

        config = RAGConfig(llm_mode=ModelMode.LOCAL, embedding_provider="openai")
        with pytest.raises(ValueError, match="local embedding provider"):
            config.ensure_local_only()

    def test_passes_for_local_config(self):
        """ensure_local_only() passes for valid local-only configurations."""
        from tools.rag.config import ModelMode, RAGConfig

        for provider in ("ollama", "huggingface", "simple"):
            config = RAGConfig(llm_mode=ModelMode.LOCAL, embedding_provider=provider)
            config.ensure_local_only()  # Should not raise

    def test_not_a_noop(self):
        """ensure_local_only() is NOT a no-op — it must actually check something."""
        from tools.rag.config import ModelMode, RAGConfig

        config = RAGConfig(llm_mode=ModelMode.EXTERNAL)
        # If this doesn't raise, the method is still a no-op (regression)
        with pytest.raises(ValueError):
            config.ensure_local_only()


# ---------------------------------------------------------------------------
# P3: OnDemandRAGResult degradation metadata
# ---------------------------------------------------------------------------


class TestOnDemandRAGResultDegradation:
    """OnDemandRAGResult must include degradation metadata."""

    def test_result_has_degraded_field(self):
        """OnDemandRAGResult has degraded and degradation_reasons fields."""
        from tools.rag.on_demand_engine import OnDemandRAGResult

        result = OnDemandRAGResult(
            answer="test",
            context="ctx",
            sources=[],
            routing={},
            selected_files=[],
            stats={},
            degraded=True,
            degradation_reasons=["test degradation"],
        )
        assert result.degraded is True
        assert result.degradation_reasons == ["test degradation"]

    def test_result_defaults_not_degraded(self):
        """OnDemandRAGResult defaults to not degraded."""
        from tools.rag.on_demand_engine import OnDemandRAGResult

        result = OnDemandRAGResult(
            answer="test",
            context="ctx",
            sources=[],
            routing={},
            selected_files=[],
            stats={},
        )
        assert result.degraded is False
        assert result.degradation_reasons is None


# ---------------------------------------------------------------------------
# Positive exemplar: OpenAI Safety Provider pattern verification
# ---------------------------------------------------------------------------


class TestOpenAISafetyProviderExemplar:
    """Verify the OpenAI safety provider's exemplar pattern remains intact."""

    def test_result_dataclass_has_degradation_fields(self):
        """OpenAISafetyCheckResult has check_performed, degraded, origin, reason fields."""
        from grid.skills.ai_safety.providers.openai import OpenAISafetyCheckResult

        result = OpenAISafetyCheckResult(
            violations=[],
            check_performed=False,
            degraded=False,
            origin="skipped",
            reason="provider_not_enabled",
            error=None,
            request_id=None,
            retries_attempted=0,
        )
        assert result.origin == "skipped"
        assert result.check_performed is False
        assert result.degraded is False
