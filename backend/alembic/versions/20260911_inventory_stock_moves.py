"""add inventory stock move ledger

Revision ID: 20260911stockmoves
Revises: 20260911locations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260911stockmoves"
down_revision: Union[str, Sequence[str], None] = "20260911locations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory_stock_moves",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("source_location_id", sa.Integer(), nullable=True),
        sa.Column("destination_location_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("movement_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("reference", sa.String(100), nullable=True),
        sa.Column("source_module", sa.String(80), nullable=True),
        sa.Column("source_entity", sa.String(80), nullable=True),
        sa.Column("source_id", sa.String(80), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["inventory_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_location_id"], ["inventory_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["destination_location_id"], ["inventory_locations.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_stock_move_quantity"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_inventory_stock_move_unit_cost"),
        sa.CheckConstraint("movement_type IN ('receipt','issue','transfer','adjustment','opening','return')", name="ck_inventory_stock_move_type"),
        sa.CheckConstraint("status IN ('draft','posted','cancelled','reversed')", name="ck_inventory_stock_move_status"),
        sa.CheckConstraint("source_location_id IS NOT NULL OR destination_location_id IS NOT NULL", name="ck_inventory_stock_move_endpoint"),
        sa.CheckConstraint("source_location_id IS NULL OR destination_location_id IS NULL OR source_location_id <> destination_location_id", name="ck_inventory_stock_move_distinct_endpoints"),
    )
    for column in ("company_id", "item_id", "source_location_id", "destination_location_id", "reference"):
        op.create_index(f"ix_inventory_stock_moves_{column}", "inventory_stock_moves", [column])


def downgrade() -> None:
    for column in ("reference", "destination_location_id", "source_location_id", "item_id", "company_id"):
        op.drop_index(f"ix_inventory_stock_moves_{column}", table_name="inventory_stock_moves")
    op.drop_table("inventory_stock_moves")
