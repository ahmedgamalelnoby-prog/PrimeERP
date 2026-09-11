"""validate business-key uniqueness without duplicating existing constraints

Revision ID: 20260911_business_uniqueness
Revises: 20260911_shipping_settlement_guards

The commerce lifecycle migration already creates the company-scoped unique
constraints for partners and sales/purchase document numbers, while the tax
master migration creates the tax-rate constraint. Shipping carrier uniqueness
is likewise defined by the shipping schema. This revision intentionally keeps
its place in the migration chain as a no-op so upgrade head does not attempt to
create duplicate indexes/constraints.
"""

revision = "20260911_business_uniqueness"
down_revision = "20260911_shipping_settlement_guards"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
