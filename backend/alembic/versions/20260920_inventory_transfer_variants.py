"""Add variant support to inventory transfer lines."""
from alembic import op
import sqlalchemy as sa
revision="20260920_inventory_transfer_variants"
down_revision="20260920_merge_ar_ap_completion_heads"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("inventory_transfer_lines", sa.Column("variant_id", sa.Integer(), nullable=True))
    op.create_index("ix_inventory_transfer_lines_variant_id", "inventory_transfer_lines", ["variant_id"], unique=False)
    op.create_foreign_key("fk_inventory_transfer_lines_variant_id", "inventory_transfer_lines", "product_variants", ["variant_id"], ["id"], ondelete="RESTRICT")

def downgrade():
    op.drop_constraint("fk_inventory_transfer_lines_variant_id", "inventory_transfer_lines", type_="foreignkey")
    op.drop_index("ix_inventory_transfer_lines_variant_id", table_name="inventory_transfer_lines")
    op.drop_column("inventory_transfer_lines", "variant_id")
