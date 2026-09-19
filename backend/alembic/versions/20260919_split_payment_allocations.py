"""support one payment allocated to multiple AR/AP documents"""

from alembic import op
import sqlalchemy as sa

revision = "20260919_split_payment_allocations"
down_revision = "20260919_payment_allocations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_commerce_payment_allocation_payment", "commerce_payment_allocations", type_="unique")
    op.create_unique_constraint(
        "uq_commerce_payment_allocation_document",
        "commerce_payment_allocations",
        ["company_id", "payment_id", "document_kind", "document_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_commerce_payment_allocation_document", "commerce_payment_allocations", type_="unique")
    op.create_unique_constraint(
        "uq_commerce_payment_allocation_payment",
        "commerce_payment_allocations",
        ["payment_id"],
    )
