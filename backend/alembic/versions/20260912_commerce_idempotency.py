"""legacy compatibility migration for commerce payment idempotency

Revision ID: 20260912_commerce_idempotency
Revises: 20260912_accounting_rbac

The idempotency column and company-scoped unique index are already established
by ``20260911_commerce_payment_idempotency``. This revision remains in the
migration graph for compatibility with databases/branches that reference it,
but must not create a second copy of the same schema objects.
"""

revision = "20260912_commerce_idempotency"
down_revision = "20260912_accounting_rbac"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
