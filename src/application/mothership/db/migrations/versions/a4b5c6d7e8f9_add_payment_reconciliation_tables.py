"""Add payment webhook events and reconciliation run tables

Revision ID: a4b5c6d7e8f9
Revises: f3b4c5d6e7f8
Create Date: 2026-02-13 10:30:00

"""

from typing import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4b5c6d7e8f9"
down_revision: str | Sequence[str] | None = "f3b4c5d6e7f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "mothership_payment_webhook_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("gateway", sa.String(length=32), nullable=False, server_default="stripe"),
        sa.Column("gateway_event_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="received"),
        sa.Column("signature_hash", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("payload_hash", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("payment_transaction_id", sa.String(length=64), nullable=True),
        sa.Column("gateway_transaction_id", sa.String(length=128), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["payment_transaction_id"], ["mothership_payment_transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mothership_payment_webhook_events_gateway_event_id",
        "mothership_payment_webhook_events",
        ["gateway_event_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_payment_webhook_gateway_event",
        "mothership_payment_webhook_events",
        ["gateway", "gateway_event_id"],
    )
    op.create_index(
        "ix_mothership_payment_webhook_events_gateway_transaction_id",
        "mothership_payment_webhook_events",
        ["gateway_transaction_id"],
        unique=False,
    )
    op.create_index(
        "ix_mothership_payment_webhook_events_status",
        "mothership_payment_webhook_events",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_mothership_payment_webhook_events_received_at",
        "mothership_payment_webhook_events",
        ["received_at"],
        unique=False,
    )

    op.create_table(
        "mothership_payment_reconciliation_runs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("gateway", sa.String(length=32), nullable=False, server_default="stripe"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scanned_transactions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mismatched_transactions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("auto_reconciled_transactions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("issues", sa.JSON(), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mothership_payment_reconciliation_runs_started_at",
        "mothership_payment_reconciliation_runs",
        ["started_at"],
        unique=False,
    )

    op.create_table(
        "mothership_connect_account_mappings",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("stripe_account_id", sa.String(length=64), nullable=False),
        sa.Column("subscription_id", sa.String(length=64), nullable=True),
        sa.Column("subscription_status", sa.String(length=64), nullable=True),
        sa.Column("subscription_price_id", sa.String(length=128), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mothership_connect_account_mappings_user_id",
        "mothership_connect_account_mappings",
        ["user_id"],
        unique=True,
    )
    op.create_index(
        "ix_mothership_connect_account_mappings_stripe_account_id",
        "mothership_connect_account_mappings",
        ["stripe_account_id"],
        unique=True,
    )
    op.create_index(
        "ix_mothership_connect_account_mappings_subscription_id",
        "mothership_connect_account_mappings",
        ["subscription_id"],
        unique=False,
    )
    op.create_index(
        "ix_mothership_connect_account_mappings_subscription_status",
        "mothership_connect_account_mappings",
        ["subscription_status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_mothership_payment_reconciliation_runs_started_at",
        table_name="mothership_payment_reconciliation_runs",
    )
    op.drop_table("mothership_payment_reconciliation_runs")

    op.drop_index(
        "ix_mothership_connect_account_mappings_subscription_status",
        table_name="mothership_connect_account_mappings",
    )
    op.drop_index(
        "ix_mothership_connect_account_mappings_subscription_id",
        table_name="mothership_connect_account_mappings",
    )
    op.drop_index(
        "ix_mothership_connect_account_mappings_stripe_account_id",
        table_name="mothership_connect_account_mappings",
    )
    op.drop_index(
        "ix_mothership_connect_account_mappings_user_id",
        table_name="mothership_connect_account_mappings",
    )
    op.drop_table("mothership_connect_account_mappings")

    op.drop_index(
        "ix_mothership_payment_webhook_events_received_at",
        table_name="mothership_payment_webhook_events",
    )
    op.drop_constraint(
        "uq_payment_webhook_gateway_event",
        "mothership_payment_webhook_events",
        type_="unique",
    )
    op.drop_index(
        "ix_mothership_payment_webhook_events_status",
        table_name="mothership_payment_webhook_events",
    )
    op.drop_index(
        "ix_mothership_payment_webhook_events_gateway_transaction_id",
        table_name="mothership_payment_webhook_events",
    )
    op.drop_index(
        "ix_mothership_payment_webhook_events_gateway_event_id",
        table_name="mothership_payment_webhook_events",
    )
    op.drop_table("mothership_payment_webhook_events")
