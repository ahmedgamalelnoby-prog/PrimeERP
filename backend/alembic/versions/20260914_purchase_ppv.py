"""Add receipt allocation tracking for purchase bills.

Revision ID: 20260914_purchase_ppv
Revises: 20260914_commerce_grni

The PPV account column and foreign key are owned by
``20260914_commerce_ppv``. This migration only owns the receipt-to-bill
allocation structures, avoiding duplicate DDL when both release branches
converge.
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_purchase_ppv"
down_revision = "20260914_commerce_grni"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "purchase_bill_receipt_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bill_id", sa.Integer(), sa.ForeignKey("purchase_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("receipt_id", sa.Integer(), sa.ForeignKey("purchase_documents.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("bill_id", "receipt_id", name="uq_purchase_bill_receipt_link"),
    )
    op.create_index("ix_purchase_bill_receipt_links_company_id", "purchase_bill_receipt_links", ["company_id"])
    op.create_index("ix_purchase_bill_receipt_links_bill_id", "purchase_bill_receipt_links", ["bill_id"])
    op.create_index("ix_purchase_bill_receipt_links_receipt_id", "purchase_bill_receipt_links", ["receipt_id"])
    op.create_table(
        "purchase_bill_receipt_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bill_line_id", sa.Integer(), sa.ForeignKey("purchase_lines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("receipt_move_id", sa.Integer(), sa.ForeignKey("inventory_stock_moves.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), nullable=False),
        sa.UniqueConstraint("bill_line_id", "receipt_move_id", name="uq_purchase_bill_receipt_allocation"),
        sa.CheckConstraint("quantity > 0", name="ck_purchase_bill_receipt_allocation_quantity"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_purchase_bill_receipt_allocation_unit_cost"),
    )
    op.create_index("ix_purchase_bill_receipt_allocations_company_id", "purchase_bill_receipt_allocations", ["company_id"])
    op.create_index("ix_purchase_bill_receipt_allocations_bill_line_id", "purchase_bill_receipt_allocations", ["bill_line_id"])
    op.create_index("ix_purchase_bill_receipt_allocations_receipt_move_id", "purchase_bill_receipt_allocations", ["receipt_move_id"])


def downgrade():
    op.drop_index("ix_purchase_bill_receipt_allocations_receipt_move_id", table_name="purchase_bill_receipt_allocations")
    op.drop_index("ix_purchase_bill_receipt_allocations_bill_line_id", table_name="purchase_bill_receipt_allocations")
    op.drop_index("ix_purchase_bill_receipt_allocations_company_id", table_name="purchase_bill_receipt_allocations")
    op.drop_table("purchase_bill_receipt_allocations")
    op.drop_index("ix_purchase_bill_receipt_links_receipt_id", table_name="purchase_bill_receipt_links")
    op.drop_index("ix_purchase_bill_receipt_links_bill_id", table_name="purchase_bill_receipt_links")
    op.drop_index("ix_purchase_bill_receipt_links_company_id", table_name="purchase_bill_receipt_links")
    op.drop_table("purchase_bill_receipt_links")
