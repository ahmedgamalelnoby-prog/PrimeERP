"""add external integrations and idempotent webhook events

Revision ID: 20260911_integrations
Revises: 20260911_accounting_ledger
"""
from alembic import op
import sqlalchemy as sa

revision = '20260911_integrations'
down_revision = '20260911_accounting_ledger'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'integration_connections',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(40), nullable=False),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('base_url', sa.String(300)),
        sa.Column('credential_ref', sa.String(200)),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('last_sync_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('company_id', 'provider', 'name', name='uq_integration_company_provider_name'),
    )
    op.create_index('ix_integration_connections_company_id', 'integration_connections', ['company_id'])
    op.create_table(
        'integration_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('connection_id', sa.Integer(), sa.ForeignKey('integration_connections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('external_event_id', sa.String(160), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='received'),
        sa.Column('received_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('connection_id', 'external_event_id', name='uq_integration_event_external_id'),
    )
    op.create_index('ix_integration_events_company_id', 'integration_events', ['company_id'])
    op.create_index('ix_integration_events_connection_id', 'integration_events', ['connection_id'])

def downgrade():
    op.drop_index('ix_integration_events_connection_id', table_name='integration_events')
    op.drop_index('ix_integration_events_company_id', table_name='integration_events')
    op.drop_table('integration_events')
    op.drop_index('ix_integration_connections_company_id', table_name='integration_connections')
    op.drop_table('integration_connections')
