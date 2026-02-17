"""
Stripe payment gateway implementation.

Provides integration with Stripe payment processing.
"""

from __future__ import annotations

import logging
import os
from typing import Any

try:
    import stripe
except ImportError:
    stripe = None  # type: ignore[assignment]

from ...exceptions import IntegrationError
from ...models.payment import PaymentStatus
from .gateway import PaymentGateway as PaymentGatewayBase

logger = logging.getLogger(__name__)


class StripeGateway(PaymentGatewayBase):
    """Stripe payment gateway implementation."""

    def __init__(
        self,
        secret_key: str,
        webhook_secret: str,
        publishable_key: str | None = None,
    ):
        """
        Initialize Stripe gateway.

        Args:
            secret_key: Stripe secret key
            webhook_secret: Stripe webhook signing secret
            publishable_key: Stripe publishable key (optional)
        """
        if stripe is None:
            raise ImportError("stripe package is required. Install with: pip install stripe")

        self.secret_key = secret_key
        self.webhook_secret = webhook_secret
        self.publishable_key = publishable_key

        if secret_key:
            stripe.api_key = secret_key

    def get_name(self) -> str:
        """Get gateway name."""
        return "stripe"

    async def create_payment(
        self,
        amount_cents: int,
        currency: str,
        description: str,
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Create a Stripe payment intent."""
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                description=description,
                metadata=metadata or {},
                idempotency_key=idempotency_key,
            )

            return {
                "gateway_transaction_id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency,
                "origin": "live",
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe payment creation failed: {e}")
            raise IntegrationError(
                service="stripe",
                message=f"Payment creation failed: {str(e)}",
                details={"error_type": type(e).__name__},
            ) from e

    async def verify_webhook(self, signature: str, payload: bytes) -> dict[str, Any]:
        """Verify Stripe webhook signature."""
        try:
            event = stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
            return {
                "id": event.id,
                "type": event.type,
                "data": event.data.object.to_dict() if hasattr(event.data.object, "to_dict") else event.data.object,
                "livemode": event.livemode,
                "origin": "live",
            }
        except ValueError as e:
            logger.error(f"Invalid Stripe webhook payload: {e}")
            raise ValueError(f"Invalid webhook payload: {e}") from e
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Stripe webhook signature verification failed: {e}")
            raise ValueError(f"Invalid webhook signature: {e}") from e

    async def get_transaction_status(self, gateway_transaction_id: str) -> PaymentStatus:
        """Get Stripe payment intent status."""
        try:
            intent = stripe.PaymentIntent.retrieve(gateway_transaction_id)
            status_map = {
                "succeeded": PaymentStatus.COMPLETED,
                "processing": PaymentStatus.PROCESSING,
                "requires_payment_method": PaymentStatus.PENDING,
                "requires_confirmation": PaymentStatus.PENDING,
                "requires_action": PaymentStatus.PROCESSING,
                "requires_capture": PaymentStatus.PROCESSING,
                "canceled": PaymentStatus.CANCELLED,
            }
            return status_map.get(intent.status, PaymentStatus.PENDING)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe transaction status check failed: {e}")
            raise IntegrationError(
                service="stripe",
                message=f"Transaction status check failed: {str(e)}",
                details={"error_type": type(e).__name__},
            ) from e

    async def create_subscription(
        self,
        user_id: str,
        tier: str,
        payment_method_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a Stripe subscription."""
        try:
            # Map tier to Stripe price ID from environment (STRIPE_PRICE_STARTER, etc.)
            price_map = {
                "starter": os.getenv("STRIPE_PRICE_STARTER", "price_starter"),
                "professional": os.getenv("STRIPE_PRICE_PROFESSIONAL", "price_pro"),
                "enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE", "price_enterprise"),
            }

            price_id = price_map.get(tier.lower())
            if not price_id:
                raise ValueError(f"Invalid tier: {tier}")

            subscription_data: dict[str, Any] = {
                "items": [{"price": price_id}],
                "metadata": {**(metadata or {}), "user_id": user_id, "tier": tier},
            }

            if payment_method_id:
                subscription_data["default_payment_method"] = payment_method_id

            subscription = stripe.Subscription.create(**subscription_data)

            return {
                "gateway_subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "origin": "live",
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe subscription creation failed: {e}")
            raise IntegrationError(
                service="stripe",
                message=f"Subscription creation failed: {str(e)}",
                details={"error_type": type(e).__name__},
            ) from e

    async def cancel_subscription(self, gateway_subscription_id: str, immediately: bool = False) -> bool:
        """Cancel a Stripe subscription."""
        try:
            if immediately:
                stripe.Subscription.delete(gateway_subscription_id)
            else:
                stripe.Subscription.modify(gateway_subscription_id, cancel_at_period_end=True)
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Stripe subscription cancellation failed: {e}")
            raise IntegrationError(
                service="stripe",
                message=f"Subscription cancellation failed: {str(e)}",
                details={"error_type": type(e).__name__},
            ) from e

    async def refund(
        self,
        gateway_transaction_id: str,
        amount_cents: int | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Create a Stripe refund."""
        try:
            refund_data: dict[str, Any] = {
                "payment_intent": gateway_transaction_id,
            }
            if amount_cents:
                refund_data["amount"] = amount_cents

            if reason:
                refund_data["reason"] = reason

            refund = stripe.Refund.create(**refund_data)

            return {
                "gateway_refund_id": refund.id,
                "amount": refund.amount,
                "status": refund.status,
                "currency": refund.currency,
                "origin": "live",
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe refund failed: {e}")
            raise IntegrationError(
                service="stripe",
                message=f"Refund failed: {str(e)}",
                details={"error_type": type(e).__name__},
            ) from e
