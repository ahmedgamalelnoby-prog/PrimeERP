"""link inventory stock moves to reservations

Adds an optional reservation reference so a posting can atomically consume
the reservation that made the stock available for fulfillment.
"""
from alembic import op
import sqlalchemy as sa

revision = "20260919_stock_move_reservation"
down_revision = "20260919_payment_idempotency_constraint"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("inventory_stock_moves", sa.Column("reservation_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_inventory_stock_move_reservation",
        "inventory_stock_moves",
        "inventory_reservations",
        ["reservation_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_inventory_stock_moves_reservation_id",
        "inventory_stock_moves",
        ["reservation_id"],
    )

def downgrade() -> None:
    op.drop_index("ix_inventory_stock_moves_reservation_id", table_name="inventory_stock_moves")
    op.drop_constraint("fk_inventory_stock_move_reservation", "inventory_stock_moves", type_="foreignkey")
    op.drop_column("inventory_stock_moves", "reservation_id")
