"""create inventory transfer workflow tables

Revision ID: 20260911transfers
Revises: 20260911locstock
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911transfers"
down_revision = "20260911locstock"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_transfers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("source_warehouse_id", sa.Integer(), nullable=False),
        sa.Column("destination_warehouse_id", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_warehouse_id"], ["inventory_warehouses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["destination_warehouse_id"], ["inventory_warehouses.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("source_warehouse_id <> destination_warehouse_id", name="ck_inventory_transfer_distinct_warehouses"),
        sa.CheckConstraint("status IN ('draft','requested','approved','shipped','received','cancelled')", name="ck_inventory_transfer_status"),
    )
    op.create_index("ix_inventory_transfers_company_id", "inventory_transfers", ["company_id"])
    op.create_index("ix_inventory_transfers_reference", "inventory_transfers", ["reference"])
    op.create_index("ix_inventory_transfers_status", "inventory_transfers", ["status"])

    op.create_table(
        "inventory_transfer_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transfer_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("source_location_id", sa.Integer(), nullable=False),
        sa.Column("destination_location_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["transfer_id"], ["inventory_transfers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["inventory_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_location_id"], ["inventory_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["destination_location_id"], ["inventory_locations.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_transfer_line_quantity"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_inventory_transfer_line_cost"),
        sa.CheckConstraint("source_location_id <> destination_location_id", name="ck_inventory_transfer_line_locations"),
    )
    op.create_index("ix_inventory_transfer_lines_transfer_id", "inventory_transfer_lines", ["transfer_id"])
    op.create_index("ix_inventory_transfer_lines_item_id", "inventory_transfer_lines", ["item_id"])


def downgrade() -> None:
    op.drop_table("inventory_transfer_lines")
    op.drop_table("inventory_transfers")
