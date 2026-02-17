"""
Payment and billing domain models.

Models for transactions, subscriptions, invoices, and payment-related entities.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    id_str = str(uuid.uuid4()).replace("-", "")
    return f"{prefix}_{id_str}" if prefix else id_str


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(UTC)


class PaymentStatus(StrEnum):
    """Payment transaction status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentGateway(StrEnum):
    """Supported payment gateways."""

    STRIPE = "stripe"
    # BKASH = "bkash"  # Decommissioned


class SubscriptionTier(StrEnum):
    """Subscription tier levels."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(StrEnum):
    """Subscription status."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    EXPIRED = "expired"


@dataclass
class PaymentTransaction:
    """Represents a payment transaction."""

    id: str = field(default_factory=lambda: generate_id("pay"))
    user_id: str = ""
    amount_cents: int = 0
    currency: str = "USD"
    status: PaymentStatus = PaymentStatus.PENDING
    gateway: PaymentGateway = PaymentGateway.STRIPE
    gateway_transaction_id: str | None = None
    gateway_response: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    idempotency_key: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    completed_at: datetime | None = None
    failure_reason: str | None = None

    def is_terminal(self) -> bool:
        """Check if transaction is in a terminal state."""
        return self.status in {
            PaymentStatus.COMPLETED,
            PaymentStatus.FAILED,
            PaymentStatus.CANCELLED,
            PaymentStatus.REFUNDED,
        }

    def mark_completed(self, gateway_transaction_id: str | None = None) -> None:
        """Mark transaction as completed."""
        self.status = PaymentStatus.COMPLETED
        self.completed_at = utc_now()
        self.updated_at = utc_now()
        if gateway_transaction_id:
            self.gateway_transaction_id = gateway_transaction_id

    def mark_failed(self, reason: str) -> None:
        """Mark transaction as failed."""
        self.status = PaymentStatus.FAILED
        self.failure_reason = reason
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount_cents": self.amount_cents,
            "currency": self.currency,
            "status": self.status.value,
            "gateway": self.gateway.value,
            "gateway_transaction_id": self.gateway_transaction_id,
            "description": self.description,
            "metadata": self.metadata,
            "idempotency_key": self.idempotency_key,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "failure_reason": self.failure_reason,
        }


@dataclass
class Subscription:
    """Represents a user subscription."""

    id: str = field(default_factory=lambda: generate_id("sub"))
    user_id: str = ""
    tier: SubscriptionTier = SubscriptionTier.FREE
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    current_period_start: datetime = field(default_factory=utc_now)
    current_period_end: datetime = field(default_factory=utc_now)
    cancel_at_period_end: bool = False
    cancelled_at: datetime | None = None
    gateway: PaymentGateway = PaymentGateway.STRIPE
    gateway_subscription_id: str | None = None
    payment_method_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        if self.cancel_at_period_end and utc_now() >= self.current_period_end:
            return False
        return utc_now() < self.current_period_end

    def cancel(self) -> None:
        """Cancel the subscription at period end."""
        self.cancel_at_period_end = True
        self.cancelled_at = utc_now()
        self.updated_at = utc_now()

    def mark_cancelled(self) -> None:
        """Mark subscription as cancelled immediately."""
        self.status = SubscriptionStatus.CANCELLED
        self.cancelled_at = utc_now()
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tier": self.tier.value,
            "status": self.status.value,
            "current_period_start": self.current_period_start.isoformat(),
            "current_period_end": self.current_period_end.isoformat(),
            "cancel_at_period_end": self.cancel_at_period_end,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "gateway": self.gateway.value,
            "gateway_subscription_id": self.gateway_subscription_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class WebhookEventStatus(StrEnum):
    """Webhook processing status."""

    RECEIVED = "received"
    PROCESSED = "processed"
    IGNORED = "ignored"
    FAILED = "failed"


@dataclass
class PaymentWebhookEvent:
    """Durable webhook event record for idempotency and auditability."""

    id: str = field(default_factory=lambda: generate_id("wev"))
    gateway: PaymentGateway = PaymentGateway.STRIPE
    gateway_event_id: str = ""
    event_type: str = ""
    status: WebhookEventStatus = WebhookEventStatus.RECEIVED
    signature_hash: str = ""
    payload_hash: str = ""
    payment_transaction_id: str | None = None
    gateway_transaction_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    received_at: datetime = field(default_factory=utc_now)
    processed_at: datetime | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def mark_processed(self, payment_transaction_id: str | None = None) -> None:
        """Mark event processed successfully."""
        self.status = WebhookEventStatus.PROCESSED
        self.payment_transaction_id = payment_transaction_id
        self.processed_at = utc_now()
        self.updated_at = utc_now()

    def mark_ignored(self) -> None:
        """Mark event as intentionally ignored."""
        self.status = WebhookEventStatus.IGNORED
        self.processed_at = utc_now()
        self.updated_at = utc_now()

    def mark_failed(self, reason: str) -> None:
        """Mark event processing failed."""
        self.status = WebhookEventStatus.FAILED
        self.metadata = {**self.metadata, "failure_reason": reason}
        self.processed_at = utc_now()
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "gateway": self.gateway.value,
            "gateway_event_id": self.gateway_event_id,
            "event_type": self.event_type,
            "status": self.status.value,
            "signature_hash": self.signature_hash,
            "payload_hash": self.payload_hash,
            "payment_transaction_id": self.payment_transaction_id,
            "gateway_transaction_id": self.gateway_transaction_id,
            "metadata": self.metadata,
            "received_at": self.received_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class PaymentReconciliationRun:
    """Durable reconciliation run summary for accounting diagnostics."""

    id: str = field(default_factory=lambda: generate_id("rec"))
    gateway: PaymentGateway = PaymentGateway.STRIPE
    started_at: datetime = field(default_factory=utc_now)
    completed_at: datetime | None = None
    scanned_transactions: int = 0
    mismatched_transactions: int = 0
    auto_reconciled_transactions: int = 0
    issues: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def finish(self) -> None:
        """Finalize run timestamps."""
        self.completed_at = utc_now()
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "gateway": self.gateway.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "scanned_transactions": self.scanned_transactions,
            "mismatched_transactions": self.mismatched_transactions,
            "auto_reconciled_transactions": self.auto_reconciled_transactions,
            "issues": self.issues,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Invoice:
    """Represents an invoice/bill."""

    id: str = field(default_factory=lambda: generate_id("inv"))
    user_id: str = ""
    subscription_id: str | None = None
    amount_cents: int = 0
    currency: str = "USD"
    status: str = "draft"  # draft, open, paid, void, uncollectible
    period_start: datetime = field(default_factory=utc_now)
    period_end: datetime = field(default_factory=utc_now)
    due_date: datetime | None = None
    paid_at: datetime | None = None
    gateway_invoice_id: str | None = None
    payment_transaction_id: str | None = None
    line_items: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "subscription_id": self.subscription_id,
            "amount_cents": self.amount_cents,
            "currency": self.currency,
            "status": self.status,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "gateway_invoice_id": self.gateway_invoice_id,
            "payment_transaction_id": self.payment_transaction_id,
            "line_items": self.line_items,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
