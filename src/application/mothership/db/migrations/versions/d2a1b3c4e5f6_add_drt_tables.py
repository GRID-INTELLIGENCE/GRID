"""Add DRT tables

Revision ID: d2a1b3c4e5f6
Revises: None
Create Date: 2026-01-25 12:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2a1b3c4e5f6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Create DRT behavioral signatures table
    op.create_table(
        'drt_behavioral_signatures',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('path_pattern', sa.String(512), nullable=False, index=True),
        sa.Column('method', sa.String(16), nullable=False, index=True),
        sa.Column('headers', sa.JSON, nullable=False, default=list),
        sa.Column('body_pattern', sa.Text, nullable=True),
        sa.Column('query_pattern', sa.String(512), nullable=True),
        sa.Column('request_count', sa.Integer, nullable=False, default=0),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('retention_hours', sa.Integer, nullable=False, default=96),
        sa.Column('meta', sa.JSON, nullable=False, default=dict),
    )

    # Create composite indexes for behavioral signatures
    op.create_index(
        'ix_drt_behavioral_signatures_path_method',
        'drt_behavioral_signatures',
        ['path_pattern', 'method']
    )
    op.create_index(
        'ix_drt_behavioral_signatures_timestamp_retention',
        'drt_behavioral_signatures',
        ['timestamp', 'retention_hours']
    )

    # Create DRT attack vectors table
    op.create_table(
        'drt_attack_vectors',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('path_pattern', sa.String(512), nullable=False, index=True),
        sa.Column('method', sa.String(16), nullable=False, index=True),
        sa.Column('headers', sa.JSON, nullable=False, default=list),
        sa.Column('body_pattern', sa.Text, nullable=True),
        sa.Column('query_pattern', sa.String(512), nullable=True),
        sa.Column('severity', sa.String(32), nullable=False, default='medium'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('active', sa.Boolean, nullable=False, default=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('meta', sa.JSON, nullable=False, default=dict),
    )

    # Create composite indexes for attack vectors
    op.create_index(
        'ix_drt_attack_vectors_path_method_active',
        'drt_attack_vectors',
        ['path_pattern', 'method', 'active']
    )
    op.create_index(
        'ix_drt_attack_vectors_severity_active',
        'drt_attack_vectors',
        ['severity', 'active']
    )

    # Create DRT violations table
    op.create_table(
        'drt_violations',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('signature_id', sa.String(64), sa.ForeignKey('drt_behavioral_signatures.id'), nullable=False, index=True),
        sa.Column('attack_vector_id', sa.String(64), sa.ForeignKey('drt_attack_vectors.id'), nullable=False, index=True),
        sa.Column('similarity_score', sa.Float, nullable=False, default=0.0),
        sa.Column('request_path', sa.String(512), nullable=False),
        sa.Column('request_method', sa.String(16), nullable=False),
        sa.Column('client_ip', sa.String(64), nullable=True, index=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('was_blocked', sa.Boolean, nullable=False, default=False),
        sa.Column('action_taken', sa.String(64), nullable=False, default='escalate'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('meta', sa.JSON, nullable=False, default=dict),
    )

    # Create composite indexes for violations
    op.create_index(
        'ix_drt_violations_timestamp_score',
        'drt_violations',
        ['timestamp', 'similarity_score']
    )
    op.create_index(
        'ix_drt_violations_client_timestamp',
        'drt_violations',
        ['client_ip', 'timestamp']
    )

    # Create DRT escalated endpoints table
    op.create_table(
        'drt_escalated_endpoints',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('path', sa.String(512), nullable=False, unique=True, index=True),
        sa.Column('escalation_reason', sa.String(256), nullable=False, default='behavioral_similarity'),
        sa.Column('similarity_score', sa.Float, nullable=False, default=0.0),
        sa.Column('matched_attack_vector_id', sa.String(64), sa.ForeignKey('drt_attack_vectors.id'), nullable=True),
        sa.Column('escalation_count', sa.Integer, nullable=False, default=1),
        sa.Column('first_escalated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True, index=True),
        sa.Column('alert_sent', sa.Boolean, nullable=False, default=False),
        sa.Column('meta', sa.JSON, nullable=False, default=dict),
    )

    # Create composite indexes for escalated endpoints
    op.create_index(
        'ix_drt_escalated_endpoints_active_expires',
        'drt_escalated_endpoints',
        ['is_active', 'expires_at']
    )
    op.create_index(
        'ix_drt_escalated_endpoints_path_active',
        'drt_escalated_endpoints',
        ['path', 'is_active']
    )

    # Create DRT false positives table
    op.create_table(
        'drt_false_positives',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('violation_id', sa.String(64), sa.ForeignKey('drt_violations.id'), nullable=False, index=True),
        sa.Column('marked_by', sa.String(256), nullable=True),
        sa.Column('reason', sa.Text, nullable=True),
        sa.Column('confidence', sa.Float, nullable=False, default=1.0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('meta', sa.JSON, nullable=False, default=dict),
    )

    # Create composite indexes for false positives
    op.create_index(
        'ix_drt_false_positives_created_at',
        'drt_false_positives',
        ['created_at']
    )
    op.create_index(
        'ix_drt_false_positives_violation_marked',
        'drt_false_positives',
        ['violation_id', 'created_at']
    )

    # Create DRT false positive patterns table
    op.create_table(
        'drt_false_positive_patterns',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('path_pattern', sa.String(512), nullable=False, index=True),
        sa.Column('method', sa.String(16), nullable=False, index=True),
        sa.Column('headers', sa.JSON, nullable=False, default=list),
        sa.Column('body_pattern', sa.Text, nullable=True),
        sa.Column('query_pattern', sa.String(512), nullable=True),
        sa.Column('false_positive_count', sa.Integer, nullable=False, default=1),
        sa.Column('total_violations', sa.Integer, nullable=False, default=1),
        sa.Column('false_positive_rate', sa.Float, nullable=False, default=1.0),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False),
        sa.Column('active', sa.Boolean, nullable=False, default=True, index=True),
        sa.Column('meta', sa.JSON, nullable=False, default=dict),
    )

    # Create composite indexes for false positive patterns
    op.create_index(
        'ix_drt_false_positive_patterns_path_method',
        'drt_false_positive_patterns',
        ['path_pattern', 'method', 'active']
    )
    op.create_index(
        'ix_drt_false_positive_patterns_rate_active',
        'drt_false_positive_patterns',
        ['false_positive_rate', 'active']
    )

    # Create DRT configuration table
    op.create_table(
        'drt_configuration',
        sa.Column('id', sa.String(64), primary_key=True, default='global'),
        sa.Column('enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('similarity_threshold', sa.Float, nullable=False, default=0.85),
        sa.Column('retention_hours', sa.Integer, nullable=False, default=96),
        sa.Column('websocket_overhead', sa.Boolean, nullable=False, default=True),
        sa.Column('auto_escalate', sa.Boolean, nullable=False, default=True),
        sa.Column('escalation_timeout_minutes', sa.Integer, nullable=False, default=60),
        sa.Column('rate_limit_multiplier', sa.Float, nullable=False, default=0.5),
        sa.Column('sampling_rate', sa.Float, nullable=False, default=1.0),
        sa.Column('alert_on_escalation', sa.Boolean, nullable=False, default=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('meta', sa.JSON, nullable=False, default=dict),
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Drop tables in reverse order
    op.drop_table('drt_configuration')
    op.drop_table('drt_escalated_endpoints')
    op.drop_table('drt_violations')
    op.drop_table('drt_attack_vectors')
    op.drop_table('drt_behavioral_signatures')
