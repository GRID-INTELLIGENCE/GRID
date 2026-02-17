import asyncio
import logging
import time
from typing import Any

import stripe

from grid.config.runtime_settings import RuntimeSettings

logger = logging.getLogger(__name__)


class StripeService:
    """
    Adapter for Stripe API operations.
    Wraps synchronous Stripe calls in asyncio executors.
    Provides mock fallback if Stripe is disabled.
    """

    def __init__(self, settings: RuntimeSettings | None = None):
        runtime = settings or RuntimeSettings.from_env()
        self.api_key = runtime.payment.stripe_secret_key
        self.enabled = runtime.payment.stripe_enabled

        if self.enabled:
            if self.api_key:
                stripe.api_key = self.api_key
            else:
                logger.warning("Stripe enabled but no Secret Key provided! Service operational in mock mode only.")
                self.enabled = False

    async def create_customer(self, user_id: str, email: str, name: str | None = None) -> str | None:
        """Create a Stripe Customer."""
        if not self.enabled:
            logger.info(f"Stripe disabled. Mocking create_customer for {user_id}")
            return f"cus_mock_{user_id}"

        try:
            def _create_customer():
                params: dict[str, Any] = {"email": email, "metadata": {"user_id": user_id}}
                if name is not None:
                    params["name"] = name
                return stripe.Customer.create(**params)

            customer = await asyncio.to_thread(_create_customer)
            return customer.id
        except Exception as e:
            logger.error(f"Stripe create_customer failed: {e}")
            return None

    async def create_subscription(self, customer_id: str, price_id: str) -> dict[str, Any] | None:
        """Create a Subscription for a Customer."""
        if not self.enabled:
            return {"id": "sub_mock", "status": "active", "current_period_end": int(time.time() + 86400 * 30)}

        try:
            subscription = await asyncio.to_thread(
                lambda: stripe.Subscription.create(
                    customer=customer_id,
                    items=[{"price": price_id}],
                ),
            )
            # Return dict representation
            return subscription  # type: ignore
        except Exception as e:
            logger.error(f"Stripe create_subscription failed: {e}")
            return None

    async def report_usage(self, subscription_item_id: str, quantity: int) -> bool:
        """Report metered usage to Stripe."""
        if not self.enabled:
            return True

        try:
            await asyncio.to_thread(
                lambda: stripe.SubscriptionItem.create_usage_record(  # type: ignore[attr-defined]
                    subscription_item_id, quantity=quantity, timestamp=int(time.time()), action="increment"
                ),
            )
            return True
        except Exception as e:
            logger.error(f"Stripe report_usage failed: {e}")
            return False
