"""add canonical customers

Revision ID: 20260911customers
Revises: 20260911purchasing
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260911customers"
down_revision: Union[str, Sequence[str], None] = "20260911purchasing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sales_customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("tax_id", sa.String(100)),
        sa.Column("email", sa.String(200)),
        sa.Column("phone", sa.String(50)),
        sa.Column("address", sa.Text()),
        sa.Column("credit_limit", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("company_id", "code", name="uq_sales_customer_company_code"),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_sales_customer_name"),
        sa.CheckConstraint("length(trim(code)) > 0", name="ck_sales_customer_code"),
        sa.CheckConstraint("credit_limit >= 0", name="ck_sales_customer_credit_limit"),
    )
    op.create_index("ix_sales_customers_company_id", "sales_customers", ["company_id"])
    op.create_index("ix_sales_customers_code", "sales_customers", ["code"])


def downgrade() -> None:
    op.drop_index("ix_sales_customers_code", table_name="sales_customers")
    op.drop_index("ix_sales_customers_company_id", table_name="sales_customers")
    op.drop_table("sales_customers")
