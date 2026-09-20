"""Inventory waste workflow persistence."""
from alembic import op
import sqlalchemy as sa
revision="20260920_inventory_waste"
down_revision="20260920_inventory_transfer_variants"
branch_labels=None
depends_on=None
def upgrade():
 op.create_table("inventory_wastes",
  sa.Column("id",sa.Integer(),primary_key=True),
  sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
  sa.Column("item_id",sa.Integer(),sa.ForeignKey("inventory_items.id",ondelete="RESTRICT"),nullable=False),
  sa.Column("variant_id",sa.Integer(),sa.ForeignKey("product_variants.id",ondelete="RESTRICT"),nullable=True),
  sa.Column("location_id",sa.Integer(),sa.ForeignKey("inventory_locations.id",ondelete="RESTRICT"),nullable=False),
  sa.Column("quantity",sa.Numeric(18,4),nullable=False),
  sa.Column("unit_cost",sa.Numeric(18,4),nullable=False,server_default="0"),
  sa.Column("waste_type",sa.String(30),nullable=False),
  sa.Column("reason",sa.Text(),nullable=False),
  sa.Column("reference",sa.String(100)),
  sa.Column("status",sa.String(20),nullable=False,server_default="draft"),
  sa.Column("created_by",sa.Integer(),sa.ForeignKey("users.id",ondelete="RESTRICT"),nullable=False),
  sa.Column("posted_at",sa.DateTime(timezone=True))
 )
 op.create_index("ix_inventory_wastes_company_id","inventory_wastes",["company_id"])
 op.create_index("ix_inventory_wastes_item_id","inventory_wastes",["item_id"])
 op.create_index("ix_inventory_wastes_status","inventory_wastes",["status"])
def downgrade():
 op.drop_table("inventory_wastes")
