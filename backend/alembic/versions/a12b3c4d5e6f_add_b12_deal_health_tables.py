"""add_b12_deal_health_tables

Revision ID: a12b3c4d5e6f
Revises: e909fd4f9ed6
Create Date: 2026-09-06 03:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a12b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = 'e909fd4f9ed6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for B12 Deal Health Engine."""
    # 1. deal_health_snapshots
    op.create_table(
        'deal_health_snapshots',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('deal_id', sa.UUID(), nullable=False),
        sa.Column('health_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('classification', sa.String(length=50), nullable=False),
        sa.Column('conversion_probability', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('stall_probability', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('delay_probability', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('anomaly_detected', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('anomaly_score', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('primary_risk_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('positive_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('contributing_signals', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('feature_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('health_score >= 0 AND health_score <= 100', name=op.f('ck_deal_health_snapshots_chk_deal_health_score_range')),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_deal_health_snapshots_company_id_companies'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deal_id'], ['customer_deal_history.id'], name=op.f('fk_deal_health_snapshots_deal_id_customer_deal_history'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_deal_health_snapshots'))
    )
    op.create_index(op.f('ix_deal_health_snapshots_classification'), 'deal_health_snapshots', ['classification'], unique=False)
    op.create_index(op.f('ix_deal_health_snapshots_company_id'), 'deal_health_snapshots', ['company_id'], unique=False)
    op.create_index(op.f('ix_deal_health_snapshots_deal_id'), 'deal_health_snapshots', ['deal_id'], unique=False)
    op.create_index(op.f('ix_deal_health_snapshots_created_at'), 'deal_health_snapshots', ['created_at'], unique=False)
    op.create_index('ix_deal_health_snapshots_company_deal', 'deal_health_snapshots', ['company_id', 'deal_id'], unique=False)

    # 2. deal_health_alerts
    op.create_table(
        'deal_health_alerts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('deal_id', sa.UUID(), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), server_default='HIGH', nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('health_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('anomaly_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('recommended_action', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE', nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_deal_health_alerts_actor_id_users'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_deal_health_alerts_company_id_companies'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deal_id'], ['customer_deal_history.id'], name=op.f('fk_deal_health_alerts_deal_id_customer_deal_history'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_deal_health_alerts'))
    )
    op.create_index(op.f('ix_deal_health_alerts_actor_id'), 'deal_health_alerts', ['actor_id'], unique=False)
    op.create_index(op.f('ix_deal_health_alerts_alert_type'), 'deal_health_alerts', ['alert_type'], unique=False)
    op.create_index(op.f('ix_deal_health_alerts_company_id'), 'deal_health_alerts', ['company_id'], unique=False)
    op.create_index(op.f('ix_deal_health_alerts_deal_id'), 'deal_health_alerts', ['deal_id'], unique=False)
    op.create_index(op.f('ix_deal_health_alerts_severity'), 'deal_health_alerts', ['severity'], unique=False)
    op.create_index(op.f('ix_deal_health_alerts_status'), 'deal_health_alerts', ['status'], unique=False)
    op.create_index(op.f('ix_deal_health_alerts_created_at'), 'deal_health_alerts', ['created_at'], unique=False)
    op.create_index('ix_deal_health_alerts_company_status', 'deal_health_alerts', ['company_id', 'status'], unique=False)
    op.create_index('ix_deal_health_alerts_deal_type_status', 'deal_health_alerts', ['deal_id', 'alert_type', 'status'], unique=False)

    # 3. deal_health_recommendations
    op.create_table(
        'deal_health_recommendations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('deal_id', sa.UUID(), nullable=False),
        sa.Column('recommendation_type', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=20), server_default='MEDIUM', nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('triggering_signal', sa.String(length=100), nullable=False),
        sa.Column('suggested_action', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_deal_health_recommendations_company_id_companies'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deal_id'], ['customer_deal_history.id'], name=op.f('fk_deal_health_recommendations_deal_id_customer_deal_history'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_deal_health_recommendations'))
    )
    op.create_index(op.f('ix_deal_health_recommendations_company_id'), 'deal_health_recommendations', ['company_id'], unique=False)
    op.create_index(op.f('ix_deal_health_recommendations_deal_id'), 'deal_health_recommendations', ['deal_id'], unique=False)
    op.create_index(op.f('ix_deal_health_recommendations_recommendation_type'), 'deal_health_recommendations', ['recommendation_type'], unique=False)
    op.create_index('ix_deal_health_recs_company_deal', 'deal_health_recommendations', ['company_id', 'deal_id'], unique=False)
    op.create_index('ix_deal_health_recs_status', 'deal_health_recommendations', ['status'], unique=False)

    # 4. deal_health_nudges
    op.create_table(
        'deal_health_nudges',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('deal_id', sa.UUID(), nullable=False),
        sa.Column('nudge_type', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('recipient_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_deal_health_nudges_actor_id_users'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_deal_health_nudges_company_id_companies'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deal_id'], ['customer_deal_history.id'], name=op.f('fk_deal_health_nudges_deal_id_customer_deal_history'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], name=op.f('fk_deal_health_nudges_recipient_id_users'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_deal_health_nudges'))
    )
    op.create_index(op.f('ix_deal_health_nudges_actor_id'), 'deal_health_nudges', ['actor_id'], unique=False)
    op.create_index(op.f('ix_deal_health_nudges_company_id'), 'deal_health_nudges', ['company_id'], unique=False)
    op.create_index(op.f('ix_deal_health_nudges_deal_id'), 'deal_health_nudges', ['deal_id'], unique=False)
    op.create_index(op.f('ix_deal_health_nudges_recipient_id'), 'deal_health_nudges', ['recipient_id'], unique=False)
    op.create_index('ix_deal_health_nudges_company_deal', 'deal_health_nudges', ['company_id', 'deal_id'], unique=False)
    op.create_index('ix_deal_health_nudges_status', 'deal_health_nudges', ['status'], unique=False)

    # 5. deal_health_escalations
    op.create_table(
        'deal_health_escalations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('deal_id', sa.UUID(), nullable=False),
        sa.Column('current_health', sa.String(length=50), nullable=False),
        sa.Column('escalation_reason', sa.Text(), nullable=False),
        sa.Column('source_signal', sa.String(length=100), nullable=False),
        sa.Column('previous_authority_id', sa.UUID(), nullable=True),
        sa.Column('next_authority_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('sla_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_deal_health_escalations_company_id_companies'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deal_id'], ['customer_deal_history.id'], name=op.f('fk_deal_health_escalations_deal_id_customer_deal_history'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['next_authority_id'], ['users.id'], name=op.f('fk_deal_health_escalations_next_authority_id_users'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['previous_authority_id'], ['users.id'], name=op.f('fk_deal_health_escalations_previous_authority_id_users'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_deal_health_escalations'))
    )
    op.create_index(op.f('ix_deal_health_escalations_company_id'), 'deal_health_escalations', ['company_id'], unique=False)
    op.create_index(op.f('ix_deal_health_escalations_deal_id'), 'deal_health_escalations', ['deal_id'], unique=False)
    op.create_index(op.f('ix_deal_health_escalations_next_authority_id'), 'deal_health_escalations', ['next_authority_id'], unique=False)
    op.create_index(op.f('ix_deal_health_escalations_previous_authority_id'), 'deal_health_escalations', ['previous_authority_id'], unique=False)
    op.create_index('ix_deal_health_escalations_company_deal', 'deal_health_escalations', ['company_id', 'deal_id'], unique=False)
    op.create_index('ix_deal_health_escalations_status', 'deal_health_escalations', ['status'], unique=False)

    # 6. deal_health_model_metadata
    op.create_table(
        'deal_health_model_metadata',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('model_type', sa.String(length=50), server_default='DEAL_HEALTH_ENSEMBLE', nullable=False),
        sa.Column('trained_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('feature_names', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_deal_health_model_metadata_company_id_companies'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_deal_health_model_metadata'))
    )
    op.create_index(op.f('ix_deal_health_model_metadata_company_id'), 'deal_health_model_metadata', ['company_id'], unique=False)
    op.create_index('ix_deal_health_model_metadata_company_version', 'deal_health_model_metadata', ['company_id', 'model_version'], unique=False)


def downgrade() -> None:
    """Downgrade schema for B12 Deal Health Engine."""
    op.drop_table('deal_health_model_metadata')
    op.drop_table('deal_health_escalations')
    op.drop_table('deal_health_nudges')
    op.drop_table('deal_health_recommendations')
    op.drop_table('deal_health_alerts')
    op.drop_table('deal_health_snapshots')
