"""
Payment and billing schemas.

Pydantic schemas for payment-related API requests and responses.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from ..schemas import BaseSchema


class PaymentStatusSchema(str, Enum):
    """Payment status for API responses."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentGatewaySchema(str, Enum):
    """Payment gateway types."""

    STRIPE = "stripe"
    # BKASH = "bkash"  # Decommissioned


class SubscriptionTierSchema(str, Enum):
    """Subscription tier levels."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatusSchema(str, Enum):
    """Subscription status."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    EXPIRED = "expired"


# Payment Request Schemas
class CreatePaymentRequest(BaseSchema):
    """Request to create a payment."""

    amount_cents: int = Field(..., description="Amount in cents", gt=0)
    currency: str = Field(default="USD", description="Currency code")
    description: str = Field(..., description="Payment description")
    gateway: PaymentGatewaySchema | None = Field(None, description="Payment gateway (defaults to configured gateway)")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class RefundPaymentRequest(BaseSchema):
    """Request to refund a payment."""

    transaction_id: str = Field(..., description="Transaction ID to refund")
    amount_cents: int | None = Field(None, description="Amount to refund in cents (None for full refund)", gt=0)
    reason: str | None = Field(None, description="Reason for refund")


# Subscription Request Schemas
class CreateSubscriptionRequest(BaseSchema):
    """Request to create a subscription."""

    tier: SubscriptionTierSchema = Field(..., description="Subscription tier")
    payment_method_id: str | None = Field(None, description="Payment method ID from gateway")
    gateway: PaymentGatewaySchema | None = Field(None, description="Payment gateway (defaults to configured gateway)")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class CancelSubscriptionRequest(BaseSchema):
    """Request to cancel a subscription."""

    subscription_id: str = Field(..., description="Subscription ID to cancel")
    immediately: bool = Field(False, description="Cancel immediately or at period end")


# Payment Response Schemas
class PaymentTransactionResponse(BaseSchema):
    """Payment transaction response."""

    id: str
    user_id: str
    amount_cents: int
    currency: str
    status: PaymentStatusSchema
    gateway: PaymentGatewaySchema
    gateway_transaction_id: str | None = None
    description: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    failure_reason: str | None = None


class SubscriptionResponse(BaseSchema):
    """Subscription response."""

    id: str
    user_id: str
    tier: SubscriptionTierSchema
    status: SubscriptionStatusSchema
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    cancelled_at: datetime | None = None
    gateway: PaymentGatewaySchema
    gateway_subscription_id: str | None = None
    created_at: datetime
    updated_at: datetime


class InvoiceResponse(BaseSchema):
    """Invoice response."""

    id: str
    user_id: str
    subscription_id: str | None = None
    amount_cents: int
    currency: str
    status: str
    period_start: datetime
    period_end: datetime
    due_date: datetime | None = None
    paid_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CreatePaymentResponse(BaseSchema):
    """Response after creating a payment."""

    transaction: PaymentTransactionResponse
    client_secret: str | None = Field(None, description="Client secret for payment confirmation (Stripe)")
    payment_url: str | None = Field(None, description="Payment URL for redirect")


class RefundResponse(BaseSchema):
    """Response after creating a refund."""

    refund_id: str
    transaction_id: str
    amount_cents: int
    status: str
    created_at: datetime


# Webhook Schemas
class WebhookEventRequest(BaseModel):
    """Webhook event payload (raw, will be verified)."""

    payload: bytes = Field(..., description="Raw webhook payload")


class WebhookEventResponse(BaseSchema):
    """Webhook event processing response."""

    processed: bool
    event_type: str
    event_id: str | None = None
    message: str
