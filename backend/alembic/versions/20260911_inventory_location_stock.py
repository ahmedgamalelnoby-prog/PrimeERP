"""create location-level inventory balances

Revision ID: 20260911locstock
Revises: 20260911stockmoves
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911locstock"
down_revision = "20260911stockmoves"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_location_stocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("quantity_on_hand", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("quantity_reserved", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["inventory_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["item_id"], ["inventory_items.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("company_id", "location_id", "item_id", name="uq_inventory_location_stock"),
        sa.CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_location_stock_on_hand"),
        sa.CheckConstraint("quantity_reserved >= 0", name="ck_inventory_location_stock_reserved"),
    )
    op.create_index("ix_inventory_location_stocks_company_id", "inventory_location_stocks", ["company_id"])
    op.create_index("ix_inventory_location_stocks_location_id", "inventory_location_stocks", ["location_id"])
    op.create_index("ix_inventory_location_stocks_item_id", "inventory_location_stocks", ["item_id"])


def downgrade() -> None:
    op.drop_table("inventory_location_stocks")
