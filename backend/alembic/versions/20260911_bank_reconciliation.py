"""add bank reconciliation accounts and statement lines"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision: str = "20260911bankrecon"
down_revision: Union[str, Sequence[str], None] = "20260911treasury"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("bank_accounts", sa.Column("id",sa.Integer(),primary_key=True), sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False), sa.Column("code",sa.String(40),nullable=False), sa.Column("name",sa.String(120),nullable=False), sa.Column("currency_code",sa.String(3),nullable=False,server_default="EGP"), sa.Column("opening_balance",sa.Numeric(18,4),nullable=False,server_default="0"), sa.Column("is_active",sa.Integer(),nullable=False,server_default="1"), sa.UniqueConstraint("company_id","code",name="uq_bank_account_company_code"))
    op.create_index("ix_bank_accounts_company_id","bank_accounts",["company_id"])
    op.create_table("bank_statement_lines", sa.Column("id",sa.Integer(),primary_key=True), sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False), sa.Column("bank_account_id",sa.Integer(),sa.ForeignKey("bank_accounts.id",ondelete="CASCADE"),nullable=False), sa.Column("statement_date",sa.Date(),nullable=False), sa.Column("value_date",sa.Date()), sa.Column("reference",sa.String(120)), sa.Column("description",sa.Text()), sa.Column("amount",sa.Numeric(18,4),nullable=False), sa.Column("direction",sa.String(10),nullable=False), sa.Column("status",sa.String(20),nullable=False,server_default="unmatched"), sa.Column("matched_payment_id",sa.Integer(),sa.ForeignKey("treasury_payments.id",ondelete="SET NULL")), sa.CheckConstraint("direction IN ('credit','debit')",name="ck_bank_statement_direction"), sa.CheckConstraint("status IN ('unmatched','matched')",name="ck_bank_statement_status"))
    for c in ("company_id","bank_account_id","status"): op.create_index(f"ix_bank_statement_lines_{c}","bank_statement_lines",[c])
    op.create_index("ix_bank_statement_account_date","bank_statement_lines",["bank_account_id","statement_date"])

def downgrade() -> None:
    op.drop_index("ix_bank_statement_account_date",table_name="bank_statement_lines")
    for c in ("status","bank_account_id","company_id"): op.drop_index(f"ix_bank_statement_lines_{c}",table_name="bank_statement_lines")
    op.drop_table("bank_statement_lines"); op.drop_index("ix_bank_accounts_company_id",table_name="bank_accounts"); op.drop_table("bank_accounts")
