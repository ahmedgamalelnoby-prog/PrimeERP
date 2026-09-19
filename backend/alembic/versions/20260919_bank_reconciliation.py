"""add bank accounts, statements and reconciliation workflow"""
from alembic import op
import sqlalchemy as sa

revision = "20260919_bank_reconciliation"
down_revision = "20260911_commerce_payment_idempotency"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("treasury_bank_accounts",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("account_combination_id",sa.Integer(),sa.ForeignKey("account_combinations.id",ondelete="RESTRICT")),
        sa.Column("name",sa.String(150),nullable=False),sa.Column("bank_name",sa.String(150),nullable=False),
        sa.Column("account_number",sa.String(100)),sa.Column("currency",sa.String(10),server_default="EGP",nullable=False),
        sa.Column("opening_balance",sa.Numeric(18,4),server_default="0",nullable=False),sa.Column("is_active",sa.Boolean(),server_default=sa.true(),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.UniqueConstraint("company_id","name",name="uq_treasury_bank_account_company_name"))
    op.create_index("ix_treasury_bank_accounts_company_id","treasury_bank_accounts",["company_id"])
    op.create_table("treasury_bank_statements",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("bank_account_id",sa.Integer(),sa.ForeignKey("treasury_bank_accounts.id",ondelete="CASCADE"),nullable=False),
        sa.Column("statement_number",sa.String(100),nullable=False),sa.Column("period_start",sa.Date(),nullable=False),sa.Column("period_end",sa.Date(),nullable=False),
        sa.Column("opening_balance",sa.Numeric(18,4),nullable=False),sa.Column("closing_balance",sa.Numeric(18,4),nullable=False),sa.Column("status",sa.String(20),server_default="open",nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.UniqueConstraint("bank_account_id","statement_number",name="uq_treasury_bank_statement_number"),sa.CheckConstraint("period_end >= period_start",name="ck_treasury_bank_statement_dates"),sa.CheckConstraint("status IN ('open','closed')",name="ck_treasury_bank_statement_status"))
    op.create_index("ix_treasury_bank_statements_company_id","treasury_bank_statements",["company_id"])
    op.create_table("treasury_bank_statement_lines",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("statement_id",sa.Integer(),sa.ForeignKey("treasury_bank_statements.id",ondelete="CASCADE"),nullable=False),
        sa.Column("external_id",sa.String(160)),sa.Column("fingerprint",sa.String(64),nullable=False),sa.Column("transaction_date",sa.Date(),nullable=False),sa.Column("value_date",sa.Date()),
        sa.Column("description",sa.Text()),sa.Column("reference",sa.String(150)),sa.Column("cheque_number",sa.String(100)),sa.Column("debit",sa.Numeric(18,4),server_default="0",nullable=False),sa.Column("credit",sa.Numeric(18,4),server_default="0",nullable=False),
        sa.Column("currency",sa.String(10),server_default="EGP",nullable=False),sa.Column("matched_amount",sa.Numeric(18,4),server_default="0",nullable=False),sa.Column("status",sa.String(20),server_default="unmatched",nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.UniqueConstraint("statement_id","fingerprint",name="uq_treasury_statement_line_fingerprint"),sa.CheckConstraint("debit >= 0 AND credit >= 0",name="ck_treasury_statement_line_nonnegative"),sa.CheckConstraint("NOT (debit > 0 AND credit > 0)",name="ck_treasury_statement_line_one_side"),sa.CheckConstraint("matched_amount >= 0",name="ck_treasury_statement_line_matched"),sa.CheckConstraint("status IN ('unmatched','partial','matched')",name="ck_treasury_statement_line_status"))
    op.create_index("ix_treasury_bank_statement_lines_company_id","treasury_bank_statement_lines",["company_id"])
    op.create_table("treasury_reconciliation_sessions",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("bank_account_id",sa.Integer(),sa.ForeignKey("treasury_bank_accounts.id",ondelete="RESTRICT"),nullable=False),sa.Column("statement_id",sa.Integer(),sa.ForeignKey("treasury_bank_statements.id",ondelete="RESTRICT"),nullable=False,unique=True),
        sa.Column("book_balance",sa.Numeric(18,4),server_default="0",nullable=False),sa.Column("bank_balance",sa.Numeric(18,4),server_default="0",nullable=False),sa.Column("difference",sa.Numeric(18,4),server_default="0",nullable=False),sa.Column("status",sa.String(20),server_default="open",nullable=False),
        sa.Column("closed_by",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("closed_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.CheckConstraint("status IN ('open','balanced','closed')",name="ck_treasury_reconciliation_status"))
    op.create_index("ix_treasury_reconciliation_sessions_company_id","treasury_reconciliation_sessions",["company_id"])
    op.create_table("treasury_reconciliation_matches",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("session_id",sa.Integer(),sa.ForeignKey("treasury_reconciliation_sessions.id",ondelete="CASCADE"),nullable=False),sa.Column("statement_line_id",sa.Integer(),sa.ForeignKey("treasury_bank_statement_lines.id",ondelete="CASCADE"),nullable=False),
        sa.Column("source_type",sa.String(30),nullable=False),sa.Column("source_id",sa.Integer(),nullable=False),sa.Column("amount",sa.Numeric(18,4),nullable=False),sa.Column("created_by",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.UniqueConstraint("statement_line_id","source_type","source_id",name="uq_treasury_reconciliation_match_source"),sa.CheckConstraint("amount > 0",name="ck_treasury_reconciliation_match_amount"))
    op.create_index("ix_treasury_reconciliation_matches_session_id","treasury_reconciliation_matches",["session_id"])
def downgrade():
    op.drop_table("treasury_reconciliation_matches");op.drop_table("treasury_reconciliation_sessions");op.drop_table("treasury_bank_statement_lines");op.drop_table("treasury_bank_statements");op.drop_table("treasury_bank_accounts")
