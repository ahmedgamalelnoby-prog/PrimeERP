"""add hierarchical inventory warehouse locations

Revision ID: 20260911locations
Revises: 20260911warehouse
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260911locations"
down_revision: Union[str, Sequence[str], None] = "20260911warehouse"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory_locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("location_type", sa.String(length=30), nullable=False, server_default="storage"),
        sa.Column("is_virtual", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["inventory_warehouses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["inventory_locations.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("warehouse_id", "code", name="uq_inventory_location_warehouse_code"),
        sa.CheckConstraint(
            "location_type IN ('storage','receiving','shipping','quarantine','damaged','transit','virtual')",
            name="ck_inventory_location_type",
        ),
    )
    op.create_index("ix_inventory_locations_company_id", "inventory_locations", ["company_id"])
    op.create_index("ix_inventory_locations_warehouse_id", "inventory_locations", ["warehouse_id"])
    op.create_index("ix_inventory_locations_parent_id", "inventory_locations", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_inventory_locations_parent_id", table_name="inventory_locations")
    op.drop_index("ix_inventory_locations_warehouse_id", table_name="inventory_locations")
    op.drop_index("ix_inventory_locations_company_id", table_name="inventory_locations")
    op.drop_table("inventory_locations")
