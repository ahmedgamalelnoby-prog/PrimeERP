"""Add sales return allocation tracking for controlled physical returns.

Revision ID: 20260914_sales_returns
Revises: 20260914_commerce_ppv
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_sales_returns"
down_revision = "20260914_commerce_ppv"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sales_return_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("credit_note_line_id", sa.Integer(), nullable=False),
        sa.Column("original_delivery_line_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["credit_note_line_id"], ["sales_lines.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["original_delivery_line_id"], ["sales_lines.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("credit_note_line_id", "original_delivery_line_id", name="uq_sales_return_allocation_line"),
        sa.CheckConstraint("quantity > 0", name="ck_sales_return_allocation_quantity"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_sales_return_allocation_unit_cost"),
    )
    op.create_index("ix_sales_return_allocations_company_id", "sales_return_allocations", ["company_id"])
    op.create_index("ix_sales_return_allocations_credit_note_line_id", "sales_return_allocations", ["credit_note_line_id"])
    op.create_index("ix_sales_return_allocations_original_delivery_line_id", "sales_return_allocations", ["original_delivery_line_id"])


def downgrade():
    op.drop_index("ix_sales_return_allocations_original_delivery_line_id", table_name="sales_return_allocations")
    op.drop_index("ix_sales_return_allocations_credit_note_line_id", table_name="sales_return_allocations")
    op.drop_index("ix_sales_return_allocations_company_id", table_name="sales_return_allocations")
    op.drop_table("sales_return_allocations")
