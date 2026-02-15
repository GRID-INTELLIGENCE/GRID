"""create password_history table

Revision ID: 002_password_history
Revises: 001_initial
Create Date: 2026-02-13 05:53:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = '002_password_history'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create password_history table
    op.create_table('password_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_password_history_id'), 'password_history', ['id'], unique=False)
    op.create_index('ix_password_history_user_id_created_at', 'password_history', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_password_history_user_id_created_at', table_name='password_history')
    op.drop_index(op.f('ix_password_history_id'), table_name='password_history')

    # Drop table
    op.drop_table('password_history')
