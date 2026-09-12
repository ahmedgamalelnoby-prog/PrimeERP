"""merge all remaining Alembic release-gate heads

This is a structural merge only. All six existing heads already contain their
own schema/data changes; this revision only establishes one canonical upgrade
path for fresh databases and for ``alembic check``.

Revision ID: 20260912_release_gate_heads_merge
Revises: 20260911_commerce_payment_idempotency, 20260911_security_inventory_merge, 20260911_tenant_owner_role, 20260911_treasury_heads_merge, 20260912_document_number_constraints, 20260912_integration_mappings
"""

revision = "20260912_release_gate_heads_merge"
down_revision = (
    "20260911_commerce_payment_idempotency",
    "20260911_security_inventory_merge",
    "20260911_tenant_owner_role",
    "20260911_treasury_heads_merge",
    "20260912_document_number_constraints",
    "20260912_integration_mappings",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
