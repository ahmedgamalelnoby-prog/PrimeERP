"""add AR/AP payment allocations"""
from alembic import op
import sqlalchemy as sa

revision = "20260919_payment_allocations"
down_revision = "20260919_ar_ap_due_dates"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "commerce_payment_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("commerce_payments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("document_kind", sa.String(length=10), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("payment_id", name="uq_commerce_payment_allocation_payment"),
        sa.CheckConstraint("document_kind IN ('sale','purchase')", name="ck_commerce_payment_allocation_kind"),
        sa.CheckConstraint("amount > 0", name="ck_commerce_payment_allocation_amount"),
        sa.CheckConstraint("status IN ('active','reversed')", name="ck_commerce_payment_allocation_status"),
    )
    op.create_index("ix_commerce_payment_allocations_company_id","commerce_payment_allocations",["company_id"])
    op.create_index("ix_commerce_payment_allocations_document_id","commerce_payment_allocations",["document_id"])

def downgrade() -> None:
    op.drop_index("ix_commerce_payment_allocations_document_id",table_name="commerce_payment_allocations")
    op.drop_index("ix_commerce_payment_allocations_company_id",table_name="commerce_payment_allocations")
    op.drop_table("commerce_payment_allocations")
