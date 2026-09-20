"""inventory cost variance

Revision ID: 20260920_cost_mrp_completion
Revises: 20260920_wms_reservation_backorder_completion
"""
from alembic import op
import sqlalchemy as sa

revision = "20260920_cost_mrp_completion"
down_revision = "20260920_wms_reservation_backorder_completion"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "inventory_cost_variances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            sa.Integer(),
            sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "warehouse_id",
            sa.Integer(),
            sa.ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "variant_id",
            sa.Integer(),
            sa.ForeignKey("product_variants.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("standard_unit_cost", sa.Numeric(18, 6), nullable=False),
        sa.Column("actual_unit_cost", sa.Numeric(18, 6), nullable=False),
        sa.Column("variance_value", sa.Numeric(18, 4), nullable=False),
        sa.Column("basis", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "journal_entry_id",
            sa.Integer(),
            sa.ForeignKey("journal_entries.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_inventory_cost_variances_company_id",
        "inventory_cost_variances",
        ["company_id"],
    )
    op.create_index(
        "ix_inventory_cost_variances_item_id",
        "inventory_cost_variances",
        ["item_id"],
    )
    op.create_index(
        "ix_inventory_cost_variances_warehouse_id",
        "inventory_cost_variances",
        ["warehouse_id"],
        )
    op.create_index(
        "ix_inventory_cost_variances_variant_id",
        "inventory_cost_variances",
        ["variant_id"],
    )


def downgrade():
    op.drop_table("inventory_cost_variances")
