"""add ledger and tax tables

Revision ID: 20260911_accounting_ledger
Revises: 20260911enterprise
"""
from alembic import op
import sqlalchemy as sa

revision='20260911_accounting_ledger'
down_revision='20260911enterprise'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('journal_entries',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('company_id',sa.Integer(),sa.ForeignKey('companies.id',ondelete='CASCADE'),nullable=False),sa.Column('entry_no',sa.String(60),nullable=False),sa.Column('entry_date',sa.DateTime(),nullable=False),sa.Column('source_type',sa.String(40)),sa.Column('source_id',sa.Integer()),sa.Column('description',sa.Text()),sa.Column('status',sa.String(20),nullable=False,server_default='draft'),sa.Column('total_debit',sa.Numeric(18,4),nullable=False,server_default='0'),sa.Column('total_credit',sa.Numeric(18,4),nullable=False,server_default='0'),sa.CheckConstraint("status IN ('draft','posted','reversed')",name='ck_je_status'))
    op.create_index('ix_journal_entries_company_id','journal_entries',['company_id']);op.create_index('ix_journal_entries_entry_no','journal_entries',['entry_no'])
    op.create_table('journal_lines',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('journal_entry_id',sa.Integer(),sa.ForeignKey('journal_entries.id',ondelete='CASCADE'),nullable=False),sa.Column('account_id',sa.Integer(),nullable=False),sa.Column('description',sa.String(250)),sa.Column('debit',sa.Numeric(18,4),nullable=False,server_default='0'),sa.Column('credit',sa.Numeric(18,4),nullable=False,server_default='0'),sa.CheckConstraint('debit >= 0 AND credit >= 0',name='ck_jl_nonnegative'),sa.CheckConstraint('(debit = 0) OR (credit = 0)',name='ck_jl_one_side'))
    op.create_index('ix_journal_lines_journal_entry_id','journal_lines',['journal_entry_id']);op.create_index('ix_journal_lines_account_id','journal_lines',['account_id'])
    op.create_table('tax_rates',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('company_id',sa.Integer(),sa.ForeignKey('companies.id',ondelete='CASCADE'),nullable=False),sa.Column('code',sa.String(40),nullable=False),sa.Column('name',sa.String(120),nullable=False),sa.Column('rate',sa.Numeric(8,4),nullable=False),sa.Column('tax_type',sa.String(20),nullable=False,server_default='vat'),sa.Column('is_withholding',sa.Boolean(),nullable=False,server_default='false'),sa.Column('is_active',sa.Boolean(),nullable=False,server_default='true'),sa.CheckConstraint('rate >= 0',name='ck_tax_rate_nonnegative'))
    op.create_index('ix_tax_rates_company_id','tax_rates',['company_id'])

def downgrade():
    op.drop_index('ix_tax_rates_company_id',table_name='tax_rates');op.drop_table('tax_rates');op.drop_index('ix_journal_lines_account_id',table_name='journal_lines');op.drop_index('ix_journal_lines_journal_entry_id',table_name='journal_lines');op.drop_table('journal_lines');op.drop_index('ix_journal_entries_entry_no',table_name='journal_entries');op.drop_index('ix_journal_entries_company_id',table_name='journal_entries');op.drop_table('journal_entries')
