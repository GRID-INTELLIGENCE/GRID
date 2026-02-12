"""
Abstract payment gateway interface.

Defines the contract that all payment gateway implementations must follow.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ...models.payment import PaymentStatus


class PaymentGateway(ABC):
    """
    Abstract base class for payment gateway implementations.

    All payment gateways must implement these methods to provide
    a consistent interface for payment processing.
    """

    @abstractmethod
    async def create_payment(
        self,
        amount_cents: int,
        currency: str,
        description: str,
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a payment intent/transaction.

        Args:
            amount_cents: Amount in cents
            currency: Currency code (USD, BDT, etc.)
            description: Payment description
            metadata: Optional metadata
            idempotency_key: Idempotency key to prevent duplicate payments

        Returns:
            Dictionary with payment details including gateway transaction ID
        """
        pass

    @abstractmethod
    async def verify_webhook(self, signature: str, payload: bytes) -> dict[str, Any]:
        """
        Verify webhook signature and parse payload.

        Args:
            signature: Webhook signature from headers
            payload: Raw request body

        Returns:
            Parsed webhook event data

        Raises:
            ValueError: If signature verification fails
        """
        pass

    @abstractmethod
    async def get_transaction_status(self, gateway_transaction_id: str) -> PaymentStatus:
        """
        Get the current status of a transaction.

        Args:
            gateway_transaction_id: Gateway's transaction ID

        Returns:
            Current payment status
        """
        pass

    @abstractmethod
    async def create_subscription(
        self,
        user_id: str,
        tier: str,
        payment_method_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a recurring subscription.

        Args:
            user_id: User identifier
            tier: Subscription tier (starter, professional, etc.)
            payment_method_id: Payment method ID from gateway
            metadata: Optional metadata

        Returns:
            Dictionary with subscription details including gateway subscription ID
        """
        pass

    @abstractmethod
    async def cancel_subscription(self, gateway_subscription_id: str, immediately: bool = False) -> bool:
        """
        Cancel a subscription.

        Args:
            gateway_subscription_id: Gateway's subscription ID
            immediately: If True, cancel immediately; if False, cancel at period end

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def refund(
        self,
        gateway_transaction_id: str,
        amount_cents: int | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """
        Refund a payment (full or partial).

        Args:
            gateway_transaction_id: Gateway's transaction ID
            amount_cents: Amount to refund in cents (None for full refund)
            reason: Reason for refund

        Returns:
            Dictionary with refund details
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this payment gateway."""
        pass
