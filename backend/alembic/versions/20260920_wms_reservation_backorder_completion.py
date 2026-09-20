"""WMS reservation linkage

Revision ID: 20260920_wms_reservation_backorder_completion
Revises: 20260920_crm_hr_completion
"""
from alembic import op
import sqlalchemy as sa

revision = "20260920_wms_reservation_backorder_completion"
down_revision = "20260920_crm_hr_completion"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("inventory_wms_operation_lines", sa.Column("reservation_id", sa.Integer(), nullable=True))
    op.create_index("ix_inventory_wms_operation_lines_reservation_id", "inventory_wms_operation_lines", ["reservation_id"])
    op.create_foreign_key("fk_inventory_wms_operation_lines_reservation_id", "inventory_wms_operation_lines", "inventory_reservations", ["reservation_id"], ["id"], ondelete="RESTRICT")

def downgrade():
    op.drop_constraint("fk_inventory_wms_operation_lines_reservation_id", "inventory_wms_operation_lines", type_="foreignkey")
    op.drop_index("ix_inventory_wms_operation_lines_reservation_id", table_name="inventory_wms_operation_lines")
    op.drop_column("inventory_wms_operation_lines", "reservation_id")
