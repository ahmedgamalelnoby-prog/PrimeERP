"""create inventory adjustment workflow

Revision ID: 20260911adjustments
Revises: 20260911transfers
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911adjustments"
down_revision = "20260911transfers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_adjustments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("reason", sa.String(100), nullable=False),
        sa.Column("reference", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["inventory_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["location_id"], ["inventory_locations.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_adjustment_quantity"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_inventory_adjustment_unit_cost"),
        sa.CheckConstraint("direction IN ('increase','decrease')", name="ck_inventory_adjustment_direction"),
        sa.CheckConstraint("status IN ('draft','approved','posted','cancelled')", name="ck_inventory_adjustment_status"),
    )
    op.create_index("ix_inventory_adjustments_company_id", "inventory_adjustments", ["company_id"])
    op.create_index("ix_inventory_adjustments_item_id", "inventory_adjustments", ["item_id"])
    op.create_index("ix_inventory_adjustments_location_id", "inventory_adjustments", ["location_id"])
    op.create_index("ix_inventory_adjustments_reference", "inventory_adjustments", ["reference"])
    op.create_index("ix_inventory_adjustments_status", "inventory_adjustments", ["status"])


def downgrade() -> None:
    for name in (
        "ix_inventory_adjustments_status",
        "ix_inventory_adjustments_reference",
        "ix_inventory_adjustments_location_id",
        "ix_inventory_adjustments_item_id",
        "ix_inventory_adjustments_company_id",
    ):
        op.drop_index(name, table_name="inventory_adjustments")
    op.drop_table("inventory_adjustments")
