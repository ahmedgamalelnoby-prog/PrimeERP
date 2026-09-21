"""add partial fulfillment quantities to sales and purchase lines"""
from alembic import op
import sqlalchemy as sa
revision="20260920_commerce_partial_fulfillment"
down_revision="20260920_manufacturing_pos_completion"
branch_labels=None
depends_on=None
def upgrade():
 op.add_column("sales_lines",sa.Column("fulfilled_quantity",sa.Numeric(18,4),nullable=False,server_default="0"))
 op.add_column("purchase_lines",sa.Column("fulfilled_quantity",sa.Numeric(18,4),nullable=False,server_default="0"))
def downgrade():
 op.drop_column("purchase_lines","fulfilled_quantity")
 op.drop_column("sales_lines","fulfilled_quantity")
