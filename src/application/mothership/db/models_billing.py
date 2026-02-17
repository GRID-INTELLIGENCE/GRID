from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .models_base import Base, utcnow


class APIKeyRow(Base):
    __tablename__ = "mothership_api_keys"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    key_hash: Mapped[str] = mapped_column(Text)
    key_prefix: Mapped[str] = mapped_column(String(32), index=True)
    tier: Mapped[str] = mapped_column(String(32), default="free", index=True)
    name: Mapped[str] = mapped_column(String(256), default="")
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UsageRecordRow(Base):
    __tablename__ = "mothership_usage_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    api_key_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("mothership_api_keys.id"), nullable=True)
    endpoint: Mapped[str] = mapped_column(String(512), index=True)
    cost_units: Mapped[int] = mapped_column(Integer, default=1)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class PaymentTransactionRow(Base):
    __tablename__ = "mothership_payment_transactions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(16), default="USD")
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    gateway: Mapped[str] = mapped_column(String(32), default="stripe", index=True)
    gateway_transaction_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    gateway_response: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    description: Mapped[str] = mapped_column(Text, default="")
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class SubscriptionRow(Base):
    __tablename__ = "mothership_subscriptions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    tier: Mapped[str] = mapped_column(String(32), default="free", index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    gateway: Mapped[str] = mapped_column(String(32), default="stripe", index=True)
    gateway_subscription_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    payment_method_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class InvoiceRow(Base):
    __tablename__ = "mothership_invoices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    subscription_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("mothership_subscriptions.id"), nullable=True
    )
    amount_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(16), default="USD")
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    gateway_invoice_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    payment_transaction_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("mothership_payment_transactions.id"), nullable=True
    )
    line_items: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PaymentWebhookEventRow(Base):
    __tablename__ = "mothership_payment_webhook_events"

    __table_args__ = (UniqueConstraint("gateway", "gateway_event_id", name="uq_payment_webhook_gateway_event"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    gateway: Mapped[str] = mapped_column(String(32), default="stripe", index=True)
    gateway_event_id: Mapped[str] = mapped_column(String(128), index=True)
    event_type: Mapped[str] = mapped_column(String(128), default="", index=True)
    status: Mapped[str] = mapped_column(String(32), default="received", index=True)
    signature_hash: Mapped[str] = mapped_column(String(128), default="")
    payload_hash: Mapped[str] = mapped_column(String(128), default="")
    payment_transaction_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("mothership_payment_transactions.id"), nullable=True
    )
    gateway_transaction_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PaymentReconciliationRunRow(Base):
    __tablename__ = "mothership_payment_reconciliation_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    gateway: Mapped[str] = mapped_column(String(32), default="stripe", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scanned_transactions: Mapped[int] = mapped_column(Integer, default=0)
    mismatched_transactions: Mapped[int] = mapped_column(Integer, default=0)
    auto_reconciled_transactions: Mapped[int] = mapped_column(Integer, default=0)
    issues: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ConnectAccountMappingRow(Base):
    """Maps local users to Stripe Connect account IDs for demo flows."""

    __tablename__ = "mothership_connect_account_mappings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    stripe_account_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    subscription_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    subscription_status: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    subscription_price_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
