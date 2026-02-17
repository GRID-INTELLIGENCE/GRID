from __future__ import annotations

from tests.utils.path_manager import PathManager

# Setup paths atomically to prevent race conditions
PathManager.setup_test_paths(__file__)

import pytest

from grid.billing.stripe_service import (
    CustomerResult,
    StripeService,
    SubscriptionResult,
    UsageReportResult,
)
from grid.config.runtime_settings import PaymentSettings, RuntimeSettings


def _runtime_settings_disabled() -> RuntimeSettings:
    return RuntimeSettings(
        payment=PaymentSettings(
            stripe_secret_key="",
            stripe_enabled=False,
        )
    )


def _runtime_settings_misconfigured_enabled() -> RuntimeSettings:
    return RuntimeSettings(
        payment=PaymentSettings(
            stripe_secret_key="",
            stripe_enabled=True,
        )
    )


class TestStripeServiceExplicitResults:
    """Tests for the Explicit Result pattern in StripeService."""

    def test_mock_mode_blocked_in_production(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MOTHERSHIP_ENVIRONMENT", "production")
        monkeypatch.delenv("STRIPE_ALLOW_MOCK_IN_PRODUCTION", raising=False)

        with pytest.raises(RuntimeError):
            StripeService(settings=_runtime_settings_disabled())

    def test_mock_mode_allowed_in_production_with_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MOTHERSHIP_ENVIRONMENT", "production")
        monkeypatch.setenv("STRIPE_ALLOW_MOCK_IN_PRODUCTION", "true")

        service = StripeService(settings=_runtime_settings_disabled())
        assert service.enabled is False
        assert service.is_initialized is False
        assert service.origin == "disabled"

    @pytest.mark.asyncio
    async def test_disabled_service_returns_explicit_result(self) -> None:
        service = StripeService(settings=_runtime_settings_disabled())

        # Test create_customer returns explicit result
        result = await service.create_customer("u1", "u1@example.com")
        assert isinstance(result, CustomerResult)
        assert result.id is None
        assert result.origin == "disabled"
        assert result.degraded is False
        assert result.is_simulated is False

        # Test create_subscription returns explicit result
        sub_result = await service.create_subscription("cus_test", "price_test")
        assert isinstance(sub_result, SubscriptionResult)
        assert sub_result.subscription_id is None
        assert sub_result.origin == "disabled"
        assert sub_result.degraded is False

        # Test report_usage returns explicit result
        usage_result = await service.report_usage("si_test", 1)
        assert isinstance(usage_result, UsageReportResult)
        assert usage_result.success is False
        assert usage_result.origin == "disabled"
        assert usage_result.degraded is False

    @pytest.mark.asyncio
    async def test_mock_mode_returns_degraded_result(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("STRIPE_ALLOW_MOCK_IN_PRODUCTION", "true")
        service = StripeService(settings=_runtime_settings_misconfigured_enabled())

        assert service.is_initialized is False
        assert service.origin == "mock"

        # create_customer should return mock result with degraded=True
        result = await service.create_customer("u1", "u1@example.com")
        assert isinstance(result, CustomerResult)
        assert result.id is not None
        assert result.id.startswith("cus_mock_")
        assert result.origin == "mock"
        assert result.degraded is True
        assert result.is_simulated is True
        assert result.error is not None

        # create_subscription should return mock result with degraded=True
        sub_result = await service.create_subscription("cus_test", "price_test")
        assert isinstance(sub_result, SubscriptionResult)
        assert sub_result.origin == "mock"
        assert sub_result.degraded is True
        assert sub_result.is_simulated is True

        # report_usage should return mock result with degraded=True
        usage_result = await service.report_usage("si_test", 1)
        assert isinstance(usage_result, UsageReportResult)
        assert usage_result.origin == "mock"
        assert usage_result.degraded is True
        assert usage_result.is_simulated is True


class TestStripeServiceOriginTracking:
    """Tests verifying origin tracking in different modes."""

    def test_disabled_origin(self) -> None:
        service = StripeService(settings=_runtime_settings_disabled())
        assert service.origin == "disabled"

    def test_mock_origin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("STRIPE_ALLOW_MOCK_IN_PRODUCTION", "true")
        service = StripeService(settings=_runtime_settings_misconfigured_enabled())
        assert service.origin == "mock"

    @pytest.mark.asyncio
    async def test_live_origin_with_valid_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test with valid API key - origin should be 'live'."""
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_valid")
        monkeypatch.setenv("STRIPE_ENABLED", "true")

        # This would set origin to "live" if the key was actually valid
        # We can't fully test live mode without a real key, but we verify the path
        settings = RuntimeSettings(
            payment=PaymentSettings(
                stripe_secret_key="sk_test_valid",
                stripe_enabled=True,
            )
        )
        service = StripeService(settings=settings)
        assert service.origin == "live"
