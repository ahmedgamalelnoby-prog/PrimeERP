"""Track on-hand inventory quantities by lot, serial, expiry, and location.

Revision ID: 20261102_inventory_lot_balances
Revises: 20261101_inventory_lot_serial_expiry
"""
from alembic import op
import sqlalchemy as sa

revision = "20261102_inventory_lot_balances"
down_revision = "20261101_inventory_lot_serial_expiry"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "inventory_lot_balances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("lot_number", sa.String(length=100), nullable=True),
        sa.Column("serial_number", sa.String(length=100), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("quantity_on_hand", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_lot_balance_nonnegative"),
        sa.CheckConstraint("lot_number IS NOT NULL OR serial_number IS NOT NULL", name="ck_inventory_lot_balance_identity"),
    )
    op.create_index("ix_inventory_lot_balances_id", "inventory_lot_balances", ["id"])
    for column in ("company_id", "item_id", "variant_id", "location_id", "lot_number", "serial_number", "expiry_date"):
        op.create_index(f"ix_inventory_lot_balances_{column}", "inventory_lot_balances", [column])
    op.create_index(
        "uq_inventory_lot_balance_identity",
        "inventory_lot_balances",
        [
            "company_id",
            "item_id",
            "location_id",
            sa.text("COALESCE(variant_id, 0)"),
            sa.text("COALESCE(lot_number, '')"),
            sa.text("COALESCE(serial_number, '')"),
        ],
        unique=True,
    )


def downgrade():
    op.drop_index("uq_inventory_lot_balance_identity", table_name="inventory_lot_balances")
    op.drop_index("ix_inventory_lot_balances_id", table_name="inventory_lot_balances")
    for column in ("expiry_date", "serial_number", "lot_number", "location_id", "variant_id", "item_id", "company_id"):
        op.drop_index(f"ix_inventory_lot_balances_{column}", table_name="inventory_lot_balances")
    op.drop_table("inventory_lot_balances")
