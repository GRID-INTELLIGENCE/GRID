"""Rename first_escalated_at to last_violation_at in drt_escalated_endpoints

Revision ID: e3f4a5b6c7d8
Revises: d2a1b3c4e5f6
Create Date: 2026-02-17 09:30:00

"""

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3f4a5b6c7d8"
down_revision: str | Sequence[str] | None = "d2a1b3c4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename first_escalated_at → last_violation_at to match models_drt.py."""
    op.alter_column(
        "drt_escalated_endpoints",
        "first_escalated_at",
        new_column_name="last_violation_at",
    )


def downgrade() -> None:
    """Revert last_violation_at → first_escalated_at."""
    op.alter_column(
        "drt_escalated_endpoints",
        "last_violation_at",
        new_column_name="first_escalated_at",
    )
