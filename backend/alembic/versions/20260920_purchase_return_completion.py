"""Integrated purchase return allocation lifecycle."""
from alembic import op
import sqlalchemy as sa

revision = "20260920_purchase_return_completion"
down_revision = "20260920_completion_wave2"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "purchase_return_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("debit_note_line_id", sa.Integer(), sa.ForeignKey("purchase_lines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_receipt_line_id", sa.Integer(), sa.ForeignKey("purchase_lines.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), nullable=False),
        sa.UniqueConstraint("debit_note_line_id", "original_receipt_line_id", name="uq_purchase_return_allocation_line"),
        sa.CheckConstraint("quantity > 0", name="ck_purchase_return_allocation_quantity"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_purchase_return_allocation_unit_cost"),
    )
    op.create_index("ix_purchase_return_allocations_company_id","purchase_return_allocations",["company_id"])
    op.create_index("ix_purchase_return_allocations_debit_note_line_id","purchase_return_allocations",["debit_note_line_id"])
    op.create_index("ix_purchase_return_allocations_original_receipt_line_id","purchase_return_allocations",["original_receipt_line_id"])

def downgrade():
    op.drop_index("ix_purchase_return_allocations_original_receipt_line_id", table_name="purchase_return_allocations")
    op.drop_index("ix_purchase_return_allocations_debit_note_line_id", table_name="purchase_return_allocations")
    op.drop_index("ix_purchase_return_allocations_company_id", table_name="purchase_return_allocations")
    op.drop_table("purchase_return_allocations")
