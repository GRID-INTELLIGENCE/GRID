import asyncio
import logging
import time
from typing import Any

import stripe

from src.application.mothership.config import MothershipSettings

logger = logging.getLogger(__name__)

settings = MothershipSettings.from_env()


class StripeService:
    """
    Adapter for Stripe API operations.
    Wraps synchronous Stripe calls in asyncio executors.
    Provides mock fallback if Stripe is disabled.
    """

    def __init__(self):
        self.api_key = settings.payment.stripe_secret_key
        self.enabled = settings.payment.stripe_enabled

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
            loop = asyncio.get_running_loop()
            # Use metadata to link back to our user_id
            customer = await loop.run_in_executor(
                None, lambda: stripe.Customer.create(email=email, name=name, metadata={"user_id": user_id})
            )
            return customer.id
        except Exception as e:
            logger.error(f"Stripe create_customer failed: {e}")
            return None

    async def create_subscription(self, customer_id: str, price_id: str) -> dict[str, Any] | None:
        """Create a Subscription for a Customer."""
        if not self.enabled:
            return {"id": "sub_mock", "status": "active", "current_period_end": int(time.time() + 86400 * 30)}

        try:
            loop = asyncio.get_running_loop()
            subscription = await loop.run_in_executor(
                None,
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
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: stripe.SubscriptionItem.create_usage_record(
                    subscription_item_id, quantity=quantity, timestamp=int(time.time()), action="increment"
                ),
            )
            return True
        except Exception as e:
            logger.error(f"Stripe report_usage failed: {e}")
            return False
