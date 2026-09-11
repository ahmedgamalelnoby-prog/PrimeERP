"""add unit of measure master

Revision ID: 20260911_uom
Revises: 20260911_integrations
"""
from alembic import op
import sqlalchemy as sa

revision='20260911_uom'
down_revision='20260911_integrations'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('units_of_measure',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('company_id',sa.Integer(),sa.ForeignKey('companies.id',ondelete='CASCADE'),nullable=False),
        sa.Column('code',sa.String(30),nullable=False),
        sa.Column('name',sa.String(100),nullable=False),
        sa.Column('category',sa.String(50),nullable=False),
        sa.Column('factor_to_base',sa.Numeric(18,8),nullable=False,server_default='1'),
        sa.Column('is_base',sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column('is_active',sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.UniqueConstraint('company_id','code',name='uq_uom_company_code'),
        sa.CheckConstraint('factor_to_base > 0',name='ck_uom_factor_positive'))
    op.create_index('ix_units_of_measure_company_id','units_of_measure',['company_id'])

def downgrade():
    op.drop_index('ix_units_of_measure_company_id',table_name='units_of_measure')
    op.drop_table('units_of_measure')
