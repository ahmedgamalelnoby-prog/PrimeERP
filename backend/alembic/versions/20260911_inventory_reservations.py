"""add inventory reservations

Revision ID: 20260911reservations
Revises: 20260911stockmoves
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260911reservations"
down_revision: Union[str, Sequence[str], None] = "20260911stockmoves"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory_reservations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("source_module", sa.String(80), nullable=False),
        sa.Column("source_entity", sa.String(80), nullable=False),
        sa.Column("source_id", sa.String(80), nullable=False),
        sa.Column("reference", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["inventory_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["location_id"], ["inventory_locations.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_reservation_quantity"),
        sa.CheckConstraint("status IN ('active','released','consumed','cancelled')", name="ck_inventory_reservation_status"),
    )
    for column in ("company_id", "item_id", "location_id", "status"):
        op.create_index(f"ix_inventory_reservations_{column}", "inventory_reservations", [column])


def downgrade() -> None:
    for column in ("status", "location_id", "item_id", "company_id"):
        op.drop_index(f"ix_inventory_reservations_{column}", table_name="inventory_reservations")
    op.drop_table("inventory_reservations")
