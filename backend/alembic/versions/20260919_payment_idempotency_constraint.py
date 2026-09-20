"""enforce company-scoped payment idempotency

Application-level idempotency checks must be backed by a database uniqueness
constraint so concurrent retries cannot create duplicate posted payments.
"""
from alembic import op


revision = "20260919_payment_idempotency_constraint"
down_revision = "20260919_payment_allocation_split_fix"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_commerce_payment_idempotency",
        "commerce_payments",
        ["company_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_commerce_payment_idempotency",
        "commerce_payments",
        type_="unique",
    )
