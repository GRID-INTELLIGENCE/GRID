import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Literal

import stripe

from grid.config.runtime_settings import RuntimeSettings

logger = logging.getLogger(__name__)


OriginType = Literal["live", "mock", "disabled", "error"]


@dataclass
class CustomerResult:
    """Result object for customer creation operations.

    Follows the Explicit Result pattern from OpenAISafetyCheckResult.
    Always returns full context about the operation's state.
    """

    id: str | None
    origin: OriginType
    degraded: bool
    error: str | None = None
    is_simulated: bool = False


@dataclass
class SubscriptionResult:
    """Result object for subscription creation operations."""

    subscription_id: str | None
    subscription: dict[str, Any] | None
    origin: OriginType
    degraded: bool
    error: str | None = None
    is_simulated: bool = False


@dataclass
class UsageReportResult:
    """Result object for usage reporting operations."""

    success: bool
    origin: OriginType
    degraded: bool
    error: str | None = None
    is_simulated: bool = False


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes", "y", "on"}


def _is_production_environment() -> bool:
    env = (
        os.getenv("MOTHERSHIP_ENVIRONMENT")
        or os.getenv("GRID_ENVIRONMENT")
        or os.getenv("ENVIRONMENT")
        or os.getenv("ENV")
        or "development"
    )
    return env.strip().lower() in {"production", "prod"}


class StripeServiceError(RuntimeError):
    """Raised when a Stripe operation fails unexpectedly."""


class StripeService:
    """
    Adapter for Stripe API operations with Explicit Result pattern.

    Refactored to follow the "Visibility over Resilience" philosophy:
    - All methods return explicit result objects with origin and degradation metadata
    - No silent fallbacks - callers must explicitly handle degraded states
    - Production safety: raises if misconfigured in production

    The "Explicit Result" pattern ensures the "Real World vs. Simulated World"
    boundary is strictly enforced and visible.
    """

    def __init__(self, settings: RuntimeSettings | None = None):
        runtime = settings or RuntimeSettings.from_env()
        self.api_key = runtime.payment.stripe_secret_key
        self.enabled = runtime.payment.stripe_enabled
        self._initialized = False
        self.allow_mock_in_production = _parse_bool(os.getenv("STRIPE_ALLOW_MOCK_IN_PRODUCTION"), False)

        # Determine origin based on configuration
        if self.enabled:
            if self.api_key:
                stripe.api_key = self.api_key
                self._initialized = True
                self._origin: OriginType = "live"
                logger.info("Stripe service initialized in LIVE mode")
            else:
                # Enabled but no API key - this is a configuration error
                logger.error(
                    "Stripe enabled but no Secret Key provided! "
                    "Set STRIPE_SECRET_KEY or disable Stripe via STRIPE_ENABLED=false."
                )
                self._origin = "mock"
                self.enabled = False
        else:
            self._origin = "disabled"
            logger.info("Stripe service initialized in DISABLED mode")

        # Production safety check
        if not self.enabled and _is_production_environment() and not self.allow_mock_in_production:
            raise RuntimeError(
                "StripeService is not properly configured for production. "
                "Set STRIPE_ENABLED=true with STRIPE_SECRET_KEY, or explicitly allow with "
                "STRIPE_ALLOW_MOCK_IN_PRODUCTION=true."
            )

    async def create_customer(self, user_id: str, email: str, name: str | None = None) -> CustomerResult:
        """Create a Stripe Customer with explicit result metadata.

        Returns CustomerResult with:
        - id: The customer ID (cus_xxx) or None if operation failed/degraded
        - origin: "live" (real API), "mock" (simulated), "disabled", or "error"
        - degraded: True if result is simulated or failed
        - error: Error message if degraded
        - is_simulated: True if this is not a real Stripe operation
        """
        # Handle disabled state explicitly
        if self._origin == "disabled":
            logger.info(f"Stripe disabled - returning explicit result for create_customer: {user_id}")
            return CustomerResult(
                id=None,
                origin="disabled",
                degraded=False,  # Not degraded - intentionally disabled
                error=None,
                is_simulated=False,
            )

        # Handle mock mode (enabled but no API key)
        if self._origin == "mock":
            logger.warning(f"Stripe in mock mode - returning mock result for: {email}")
            return CustomerResult(
                id=f"cus_mock_{user_id}",
                origin="mock",
                degraded=True,  # This IS degraded - caller must acknowledge
                error="Stripe service not initialized with valid API key",
                is_simulated=True,
            )

        # Live API call
        try:

            def _create_customer():
                params: dict[str, Any] = {"email": email, "metadata": {"user_id": user_id}}
                if name is not None:
                    params["name"] = name
                return stripe.Customer.create(**params)

            customer = await asyncio.to_thread(_create_customer)
            logger.info(f"Stripe customer created: {customer.id}")
            return CustomerResult(
                id=customer.id,
                origin="live",
                degraded=False,
                error=None,
                is_simulated=False,
            )
        except Exception as e:
            logger.error(f"Stripe create_customer failed: {e}")
            return CustomerResult(
                id=None,
                origin="error",
                degraded=True,
                error=str(e),
                is_simulated=False,
            )

        # Handle mock mode (shouldn't happen if properly configured, but explicit)
        if not self._initialized:
            logger.warning(f"Stripe not initialized - returning mock result for: {email}")
            return CustomerResult(
                id=f"cus_mock_{user_id}",
                origin="mock",
                degraded=True,  # This IS degraded - caller must acknowledge
                error="Stripe service not initialized with valid API key",
                is_simulated=True,
            )

        # Live API call
        try:

            def _create_customer():
                params: dict[str, Any] = {"email": email, "metadata": {"user_id": user_id}}
                if name is not None:
                    params["name"] = name
                return stripe.Customer.create(**params)

            customer = await asyncio.to_thread(_create_customer)
            logger.info(f"Stripe customer created: {customer.id}")
            return CustomerResult(
                id=customer.id,
                origin="live",
                degraded=False,
                error=None,
                is_simulated=False,
            )
        except Exception as e:
            logger.error(f"Stripe create_customer failed: {e}")
            return CustomerResult(
                id=None,
                origin="error",
                degraded=True,
                error=str(e),
                is_simulated=False,
            )

    async def create_subscription(self, customer_id: str, price_id: str) -> SubscriptionResult:
        """Create a Subscription for a Customer with explicit result metadata.

        Returns SubscriptionResult with full provenance tracking.
        """
        # Handle disabled state explicitly
        if self._origin == "disabled":
            logger.info("Stripe disabled - returning explicit result for create_subscription")
            return SubscriptionResult(
                subscription_id=None,
                subscription=None,
                origin="disabled",
                degraded=False,
                error=None,
                is_simulated=False,
            )

        # Handle mock mode (enabled but no API key)
        if self._origin == "mock":
            logger.warning(f"Stripe not initialized - returning mock subscription for: {customer_id}")
            mock_sub_id = f"sub_mock_{customer_id}"
            mock_subscription = {
                "id": mock_sub_id,
                "customer": customer_id,
                "items": {"data": [{"id": f"si_mock_{customer_id}", "price": {"id": price_id}}]},
                "status": "active",
                "mock": True,
            }
            return SubscriptionResult(
                subscription_id=mock_sub_id,
                subscription=mock_subscription,
                origin="mock",
                degraded=True,
                error="Stripe service not initialized with valid API key",
                is_simulated=True,
            )

        # Live API call
        try:
            subscription = await asyncio.to_thread(
                lambda: stripe.Subscription.create(
                    customer=customer_id,
                    items=[{"price": price_id}],
                ),
            )
            logger.info(f"Stripe subscription created: {subscription.id}")
            return SubscriptionResult(
                subscription_id=subscription.id,
                subscription=subscription,
                origin="live",
                degraded=False,
                error=None,
                is_simulated=False,
            )
        except Exception as e:
            logger.error(f"Stripe create_subscription failed: {e}")
            return SubscriptionResult(
                subscription_id=None,
                subscription=None,
                origin="error",
                degraded=True,
                error=str(e),
                is_simulated=False,
            )

    async def report_usage(self, subscription_item_id: str, quantity: int) -> UsageReportResult:
        """Report metered usage to Stripe with explicit result metadata.

        Returns UsageReportResult indicating success/failure and provenance.
        """
        # Handle disabled state explicitly
        if self._origin == "disabled":
            logger.info("Stripe disabled - returning explicit result for report_usage")
            return UsageReportResult(
                success=False,
                origin="disabled",
                degraded=False,
                error=None,
                is_simulated=False,
            )

        # Handle mock mode (enabled but no API key)
        if self._origin == "mock":
            logger.warning(f"Stripe not initialized - returning mock usage report for: {subscription_item_id}")
            return UsageReportResult(
                success=True,  # Mock "succeeds" but is clearly marked degraded
                origin="mock",
                degraded=True,
                error="Stripe service not initialized with valid API key - usage not actually reported",
                is_simulated=True,
            )

        # Live API call
        try:
            await asyncio.to_thread(
                lambda: stripe.SubscriptionItem.create_usage_record(  # type: ignore[attr-defined]
                    subscription_item_id, quantity=quantity, timestamp=int(time.time()), action="increment"
                ),
            )
            logger.debug(f"Stripe usage reported: {quantity} for {subscription_item_id}")
            return UsageReportResult(
                success=True,
                origin="live",
                degraded=False,
                error=None,
                is_simulated=False,
            )
        except Exception as e:
            logger.error(f"Stripe report_usage failed: {e}")
            return UsageReportResult(
                success=False,
                origin="error",
                degraded=True,
                error=str(e),
                is_simulated=False,
            )

    @property
    def is_initialized(self) -> bool:
        """Return whether service is properly initialized with API key."""
        return self._initialized

    @property
    def origin(self) -> OriginType:
        """Return the current origin mode of the service."""
        return self._origin
