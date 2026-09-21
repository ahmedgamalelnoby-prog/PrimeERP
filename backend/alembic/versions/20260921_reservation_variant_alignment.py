"""align inventory reservations with variant-aware reservation service.

Revision ID: 20260921_reservation_variant_alignment
Revises: 20260921_purchasing_treasury_rbac
"""

from alembic import op
import sqlalchemy as sa

revision = "20260921_reservation_variant_alignment"
down_revision = "20260921_purchasing_treasury_rbac"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "inventory_reservations",
        sa.Column("variant_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_inventory_reservations_variant_id",
        "inventory_reservations",
        "product_variants",
        ["variant_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_inventory_reservations_variant_id",
        "inventory_reservations",
        ["variant_id"],
    )


def downgrade():
    op.drop_index(
        "ix_inventory_reservations_variant_id",
        table_name="inventory_reservations",
    )
    op.drop_constraint(
        "fk_inventory_reservations_variant_id",
        "inventory_reservations",
        type_="foreignkey",
    )
    op.drop_column("inventory_reservations", "variant_id")
