"""Add cockpit tables: state, sessions, operations, components, alerts.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-03-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d3e4f5a6b7c8"
down_revision: str | None = "c2d3e4f5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mothership_cockpit_state",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("state", sa.String(32), nullable=False, index=True),
        sa.Column("version", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("total_sessions", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("active_sessions", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("total_operations", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("running_operations", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("meta", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
    )

    op.create_table(
        "mothership_cockpit_sessions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(128), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_ip", sa.String(128), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("connection_type", sa.String(32), nullable=False, server_default="http"),
        sa.Column("permissions", sa.JSON, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("active_operations", sa.JSON, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("meta", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
    )

    op.create_table(
        "mothership_cockpit_operations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("type", sa.String(64), nullable=False, index=True),
        sa.Column("name", sa.String(256), nullable=False, server_default=""),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False, index=True),
        sa.Column("priority", sa.String(32), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "session_id", sa.String(64), sa.ForeignKey("mothership_cockpit_sessions.id"), nullable=True,
        ),
        sa.Column("user_id", sa.String(128), nullable=True, index=True),
        sa.Column("parent_operation_id", sa.String(64), nullable=True),
        sa.Column("progress_percent", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("progress_message", sa.Text, nullable=False, server_default=""),
        sa.Column("steps_total", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("steps_completed", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("input_data", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("output_data", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("error_details", sa.JSON, nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("max_retries", sa.Integer, nullable=False, server_default=sa.text("3")),
        sa.Column("tags", sa.JSON, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("meta", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
    )

    op.create_table(
        "mothership_cockpit_components",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False, server_default=""),
        sa.Column("type", sa.String(64), nullable=False, server_default="service", index=True),
        sa.Column("version", sa.String(64), nullable=False, server_default=""),
        sa.Column("health", sa.String(32), nullable=False, server_default="unknown", index=True),
        sa.Column("status", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("endpoint_url", sa.Text, nullable=True),
        sa.Column("health_check_url", sa.Text, nullable=True),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_health_check", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_healthy_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uptime_seconds", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("request_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("error_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("dependencies", sa.JSON, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("tags", sa.JSON, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("meta", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
    )

    op.create_table(
        "mothership_cockpit_alerts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("severity", sa.String(32), nullable=False, index=True),
        sa.Column("title", sa.String(256), nullable=False, server_default=""),
        sa.Column("message", sa.Text, nullable=False, server_default=""),
        sa.Column("source", sa.String(128), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_acknowledged", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_resolved", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("acknowledged_by", sa.String(128), nullable=True),
        sa.Column("resolved_by", sa.String(128), nullable=True),
        sa.Column("component_id", sa.String(64), nullable=True, index=True),
        sa.Column("operation_id", sa.String(64), nullable=True, index=True),
        sa.Column("meta", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade() -> None:
    op.drop_table("mothership_cockpit_alerts")
    op.drop_table("mothership_cockpit_components")
    op.drop_table("mothership_cockpit_operations")
    op.drop_table("mothership_cockpit_sessions")
    op.drop_table("mothership_cockpit_state")
