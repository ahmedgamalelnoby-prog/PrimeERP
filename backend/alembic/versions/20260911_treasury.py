"""add treasury cash management foundation"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260911treasury"
down_revision: Union[str, Sequence[str], None] = "20260911salesquotations"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("treasury_payment_methods",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(30), nullable=False), sa.Column("name", sa.String(120), nullable=False),
        sa.Column("method_type", sa.String(30), nullable=False), sa.Column("is_incoming", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_outgoing", sa.Integer(), nullable=False, server_default="1"), sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("company_id", "code", name="uq_treasury_payment_method_company_code"))
    op.create_index("ix_treasury_payment_methods_company_id", "treasury_payment_methods", ["company_id"])
    op.create_table("treasury_payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.Integer(), sa.ForeignKey("branches.id", ondelete="RESTRICT")),
        sa.Column("payment_method_id", sa.Integer(), sa.ForeignKey("treasury_payment_methods.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("party_type", sa.String(20), nullable=False), sa.Column("party_id", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False), sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(18,4), nullable=False), sa.Column("currency_code", sa.String(3), nullable=False, server_default="EGP"),
        sa.Column("reference", sa.String(120)), sa.Column("source_module", sa.String(80)), sa.Column("source_entity", sa.String(80)), sa.Column("source_id", sa.String(80)),
        sa.Column("status", sa.String(20), nullable=False, server_default="posted"), sa.Column("reversed_payment_id", sa.Integer(), sa.ForeignKey("treasury_payments.id", ondelete="RESTRICT")),
        sa.Column("notes", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("amount > 0", name="ck_treasury_payment_amount"), sa.CheckConstraint("party_type IN ('customer','supplier','other')", name="ck_treasury_payment_party"),
        sa.CheckConstraint("direction IN ('receipt','payment')", name="ck_treasury_payment_direction"), sa.CheckConstraint("status IN ('posted','reversed')", name="ck_treasury_payment_status"))
    for column in ("company_id", "branch_id", "payment_method_id", "status"):
        op.create_index(f"ix_treasury_payments_{column}", "treasury_payments", [column])
    op.create_index("ix_treasury_payment_source", "treasury_payments", ["company_id", "source_module", "source_entity", "source_id"])

def downgrade() -> None:
    op.drop_index("ix_treasury_payment_source", table_name="treasury_payments")
    for column in ("status", "payment_method_id", "branch_id", "company_id"):
        op.drop_index(f"ix_treasury_payments_{column}", table_name="treasury_payments")
    op.drop_table("treasury_payments")
    op.drop_index("ix_treasury_payment_methods_company_id", table_name="treasury_payment_methods")
    op.drop_table("treasury_payment_methods")
