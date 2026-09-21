"""connect sales orders to inventory fulfillment
Revision ID: 20260921_sales_fulfillment
Revises: 20260921_sales_foundation
"""
from alembic import op
import sqlalchemy as sa
revision="20260921_sales_fulfillment"
down_revision="20260921_sales_foundation"
branch_labels=None
depends_on=None
def upgrade():
 op.add_column("sales_orders",sa.Column("reservation_id",sa.Integer(),nullable=True))
 op.add_column("sales_orders",sa.Column("issue_id",sa.Integer(),nullable=True))
 op.create_foreign_key("fk_sales_orders_reservation","sales_orders","stock_reservations",["reservation_id"],["id"],ondelete="SET NULL")
 op.create_foreign_key("fk_sales_orders_issue","sales_orders","stock_issues",["issue_id"],["id"],ondelete="SET NULL")
 op.create_index("ix_sales_orders_reservation","sales_orders",["reservation_id"])
 op.create_index("ix_sales_orders_issue","sales_orders",["issue_id"])
def downgrade():
 op.drop_index("ix_sales_orders_issue",table_name="sales_orders");op.drop_index("ix_sales_orders_reservation",table_name="sales_orders")
 op.drop_constraint("fk_sales_orders_issue","sales_orders",type_="foreignkey");op.drop_constraint("fk_sales_orders_reservation","sales_orders",type_="foreignkey")
 op.drop_column("sales_orders","issue_id");op.drop_column("sales_orders","reservation_id")
