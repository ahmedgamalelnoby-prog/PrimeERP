"""add product bundles

Revision ID: 20260914_product_bundles
Revises: 20260914_product_variants
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_product_bundles"
down_revision = "20260914_product_variants"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "product_bundles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name_ar", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("company_id", "code", name="uq_product_bundle_company_code"),
        sa.UniqueConstraint("company_id", "product_id", name="uq_product_bundle_company_product"),
    )
    op.create_index("ix_product_bundles_company_id", "product_bundles", ["company_id"])
    op.create_index("ix_product_bundles_product_id", "product_bundles", ["product_id"])
    op.create_table(
        "product_bundle_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bundle_id", sa.Integer(), sa.ForeignKey("product_bundles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("line_no", sa.Integer(), nullable=False),
        sa.Column("component_product_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.UniqueConstraint("bundle_id", "line_no", name="uq_product_bundle_line_no"),
        sa.UniqueConstraint("bundle_id", "component_product_id", name="uq_product_bundle_component"),
        sa.CheckConstraint("line_no > 0", name="ck_product_bundle_line_no_positive"),
        sa.CheckConstraint("quantity > 0", name="ck_product_bundle_line_quantity_positive"),
    )
    op.create_index("ix_product_bundle_lines_bundle_id", "product_bundle_lines", ["bundle_id"])
    op.create_index("ix_product_bundle_lines_component_product_id", "product_bundle_lines", ["component_product_id"])


def downgrade():
    op.drop_index("ix_product_bundle_lines_component_product_id", table_name="product_bundle_lines")
    op.drop_index("ix_product_bundle_lines_bundle_id", table_name="product_bundle_lines")
    op.drop_table("product_bundle_lines")
    op.drop_index("ix_product_bundles_product_id", table_name="product_bundles")
    op.drop_index("ix_product_bundles_company_id", table_name="product_bundles")
    op.drop_table("product_bundles")
