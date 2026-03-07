"""Add agentic cases table.

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-03-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: str | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agentic_cases",
        sa.Column("case_id", sa.String(255), primary_key=True, comment="Unique case identifier"),
        sa.Column("raw_input", sa.Text, nullable=False, comment="Original raw user input"),
        sa.Column("user_id", sa.String(255), nullable=True, comment="User identifier"),
        sa.Column("category", sa.String(100), nullable=True, comment="Case category"),
        sa.Column("priority", sa.String(50), nullable=True, server_default="medium", comment="Case priority"),
        sa.Column("confidence", sa.Float, nullable=True, comment="Classification confidence score"),
        sa.Column("structured_data", sa.JSON, nullable=True, comment="Structured case data from filing system"),
        sa.Column("labels", sa.JSON, nullable=True, comment="Case labels"),
        sa.Column("keywords", sa.JSON, nullable=True, comment="Extracted keywords"),
        sa.Column("entities", sa.JSON, nullable=True, comment="Extracted entities"),
        sa.Column("relationships", sa.JSON, nullable=True, comment="Detected relationships"),
        sa.Column("reference_file_path", sa.String(500), nullable=True, comment="Path to reference file"),
        sa.Column(
            "status", sa.String(50), nullable=False, server_default="created",
            comment="Case status: created, categorized, reference_generated, executed, completed",
        ),
        sa.Column("agent_role", sa.String(100), nullable=True, comment="Agent role used for execution"),
        sa.Column("task", sa.String(100), nullable=True, comment="Task executed"),
        sa.Column("outcome", sa.String(50), nullable=True, comment="Case outcome: success, partial, failure"),
        sa.Column("solution", sa.Text, nullable=True, comment="Solution applied"),
        sa.Column("agent_experience", sa.JSON, nullable=True, comment="Agent experience data"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now(), comment="Creation timestamp"),
        sa.Column("updated_at", sa.DateTime, nullable=True, comment="Last update timestamp"),
        sa.Column("completed_at", sa.DateTime, nullable=True, comment="Completion timestamp"),
        sa.Column("execution_time_seconds", sa.Float, nullable=True, comment="Execution time in seconds"),
    )


def downgrade() -> None:
    op.drop_table("agentic_cases")
