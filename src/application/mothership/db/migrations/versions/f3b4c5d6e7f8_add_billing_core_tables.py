"""Add billing core tables: api_keys, usage_records, payment_transactions, subscriptions, invoices.

Revision ID: f3b4c5d6e7f8
Revises: e3f4a5b6c7d8
Create Date: 2026-03-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f3b4c5d6e7f8"
down_revision: str | None = "e3f4a5b6c7d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mothership_api_keys",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(128), nullable=False, index=True),
        sa.Column("key_hash", sa.Text, nullable=False),
        sa.Column("key_prefix", sa.String(32), nullable=False, index=True),
        sa.Column("tier", sa.String(32), nullable=False, server_default="free", index=True),
        sa.Column("name", sa.String(256), nullable=False, server_default=""),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("meta", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "mothership_usage_records",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(128), nullable=False, index=True),
        sa.Column(
            "api_key_id", sa.String(64), sa.ForeignKey("mothership_api_keys.id"), nullable=True,
        ),
        sa.Column("endpoint", sa.String(512), nullable=False, index=True),
        sa.Column("cost_units", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("meta", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
    )

    op.create_table(
        "mothership_payment_transactions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(128), nullable=False, index=True),
        sa.Column("amount_cents", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(16), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending", index=True),
        sa.Column("gateway", sa.String(32), nullable=False, server_default="stripe", index=True),
        sa.Column("gateway_transaction_id", sa.String(128), nullable=True, index=True),
        sa.Column("gateway_response", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("meta", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("idempotency_key", sa.String(128), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text, nullable=True),
    )

    op.create_table(
        "mothership_subscriptions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(128), nullable=False, index=True),
        sa.Column("tier", sa.String(32), nullable=False, server_default="free", index=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active", index=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("cancel_at_period_end", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("gateway", sa.String(32), nullable=False, server_default="stripe", index=True),
        sa.Column("gateway_subscription_id", sa.String(128), nullable=True, index=True),
        sa.Column("payment_method_id", sa.String(128), nullable=True),
        sa.Column("meta", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "mothership_invoices",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(128), nullable=False, index=True),
        sa.Column(
            "subscription_id", sa.String(64), sa.ForeignKey("mothership_subscriptions.id"), nullable=True,
        ),
        sa.Column("amount_cents", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(16), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft", index=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("gateway_invoice_id", sa.String(128), nullable=True, index=True),
        sa.Column(
            "payment_transaction_id",
            sa.String(64),
            sa.ForeignKey("mothership_payment_transactions.id"),
            nullable=True,
        ),
        sa.Column("line_items", sa.JSON, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("meta", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("mothership_invoices")
    op.drop_table("mothership_subscriptions")
    op.drop_table("mothership_payment_transactions")
    op.drop_table("mothership_usage_records")
    op.drop_table("mothership_api_keys")
