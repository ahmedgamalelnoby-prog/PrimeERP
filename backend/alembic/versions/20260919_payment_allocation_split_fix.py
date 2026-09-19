"""allow multiple documents per payment allocation

The allocation model supports one payment split across multiple invoices/bills.
The original migration accidentally added a payment_id-only unique constraint,
which made the split-allocation contract impossible at database level.
"""
from alembic import op

revision = "20260919_payment_allocation_split_fix"
down_revision = "20260919_payment_allocations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_commerce_payment_allocation_payment",
        "commerce_payment_allocations",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_commerce_payment_allocation_document",
        "commerce_payment_allocations",
        ["company_id", "payment_id", "document_kind", "document_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_commerce_payment_allocation_document",
        "commerce_payment_allocations",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_commerce_payment_allocation_payment",
        "commerce_payment_allocations",
        ["payment_id"],
    )
