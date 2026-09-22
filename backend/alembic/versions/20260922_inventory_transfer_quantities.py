"""add transfer shipment and receipt quantities

The ORM transfer workflow tracks shipped and received quantities, but the
database migration was missing these columns.
"""
from alembic import op
import sqlalchemy as sa

revision = "20260922_inventory_transfer_quantities"
down_revision = "20260919_stock_move_reservation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("inventory_transfer_lines")}
    if "shipped_quantity" not in columns:
        op.add_column(
            "inventory_transfer_lines",
            sa.Column("shipped_quantity", sa.Numeric(18, 4), nullable=False, server_default="0"),
        )
    if "received_quantity" not in columns:
        op.add_column(
            "inventory_transfer_lines",
            sa.Column("received_quantity", sa.Numeric(18, 4), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("inventory_transfer_lines")}
    if "received_quantity" in columns:
        op.drop_column("inventory_transfer_lines", "received_quantity")
    if "shipped_quantity" in columns:
        op.drop_column("inventory_transfer_lines", "shipped_quantity")
