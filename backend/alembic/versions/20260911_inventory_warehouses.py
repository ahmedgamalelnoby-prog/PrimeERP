"""add branch-scoped and company-central inventory warehouses

Revision ID: 20260911warehouse
Revises: 20260831legal
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260911warehouse"
down_revision: Union[str, Sequence[str], None] = "20260831legal"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory_warehouses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_central", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("company_id", "code", name="uq_inventory_warehouse_company_code"),
        sa.CheckConstraint(
            "(is_central = true AND branch_id IS NULL) OR (is_central = false AND branch_id IS NOT NULL)",
            name="ck_inventory_warehouse_scope",
        ),
    )
    op.create_index("ix_inventory_warehouses_tenant_id", "inventory_warehouses", ["tenant_id"])
    op.create_index("ix_inventory_warehouses_company_id", "inventory_warehouses", ["company_id"])
    op.create_index("ix_inventory_warehouses_branch_id", "inventory_warehouses", ["branch_id"])

    op.add_column(
        "inventory_stocks",
        sa.Column("warehouse_id_new", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_inventory_stocks_warehouse_new",
        "inventory_stocks",
        "inventory_warehouses",
        ["warehouse_id_new"],
        ["id"],
        ondelete="RESTRICT",
    )
    # Existing inventory stock rows are intentionally not guessed into a branch.
    # They must be assigned to a real warehouse before the new FK becomes required.
    op.drop_constraint("fk_inventory_stocks_warehouse_new", "inventory_stocks", type_="foreignkey")
    op.drop_column("inventory_stocks", "warehouse_id_new")


def downgrade() -> None:
    op.drop_index("ix_inventory_warehouses_branch_id", table_name="inventory_warehouses")
    op.drop_index("ix_inventory_warehouses_company_id", table_name="inventory_warehouses")
    op.drop_index("ix_inventory_warehouses_tenant_id", table_name="inventory_warehouses")
    op.drop_table("inventory_warehouses")
