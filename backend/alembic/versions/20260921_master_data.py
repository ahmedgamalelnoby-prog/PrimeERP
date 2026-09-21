"""add tenant-safe customer and product master data
Revision ID: 20260921_master_data
Revises: 20260921_integration_mappings
"""
from alembic import op
import sqlalchemy as sa
revision="20260921_master_data"
down_revision="20260921_integration_mappings"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("customers",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("tenant_id",sa.Integer(),nullable=False),sa.Column("code",sa.String(50),nullable=False),sa.Column("name",sa.String(200),nullable=False),sa.Column("customer_type",sa.String(30),nullable=False,server_default="customer"),sa.Column("phone",sa.String(50)),sa.Column("email",sa.String(150)),sa.Column("tax_id",sa.String(100)),sa.Column("address",sa.Text()),sa.Column("credit_limit",sa.Integer(),nullable=False,server_default="0"),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("created_at",sa.TIMESTAMP(timezone=True),server_default=sa.text("now()"),nullable=False),sa.Column("updated_at",sa.TIMESTAMP(timezone=True),server_default=sa.text("now()"),nullable=False),sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"],ondelete="CASCADE"),sa.UniqueConstraint("tenant_id","code",name="uq_customers_tenant_code"))
    op.create_index("ix_customers_tenant_id","customers",["tenant_id"]);op.create_index("ix_customers_name","customers",["name"]);op.create_index("ix_customers_is_active","customers",["is_active"])
    op.create_table("product_categories",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("tenant_id",sa.Integer(),nullable=False),sa.Column("name",sa.String(150),nullable=False),sa.Column("code",sa.String(50),nullable=False),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"],ondelete="CASCADE"),sa.UniqueConstraint("tenant_id","code",name="uq_product_categories_tenant_code"))
    op.create_index("ix_product_categories_tenant_id","product_categories",["tenant_id"])
    op.create_table("product_units",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("tenant_id",sa.Integer(),nullable=False),sa.Column("name",sa.String(100),nullable=False),sa.Column("code",sa.String(30),nullable=False),sa.Column("precision",sa.Integer(),nullable=False,server_default="3"),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"],ondelete="CASCADE"),sa.UniqueConstraint("tenant_id","code",name="uq_product_units_tenant_code"))
    op.create_index("ix_product_units_tenant_id","product_units",["tenant_id"])
    op.create_table("products",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("tenant_id",sa.Integer(),nullable=False),sa.Column("category_id",sa.Integer()),sa.Column("unit_id",sa.Integer(),nullable=False),sa.Column("sku",sa.String(80),nullable=False),sa.Column("name",sa.String(200),nullable=False),sa.Column("product_type",sa.String(30),nullable=False,server_default="stock"),sa.Column("barcode",sa.String(100)),sa.Column("description",sa.Text()),sa.Column("sale_price",sa.Numeric(18,2),nullable=False,server_default="0"),sa.Column("cost_price",sa.Numeric(18,2),nullable=False,server_default="0"),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("created_at",sa.TIMESTAMP(timezone=True),server_default=sa.text("now()"),nullable=False),sa.Column("updated_at",sa.TIMESTAMP(timezone=True),server_default=sa.text("now()"),nullable=False),sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["category_id"],["product_categories.id"],ondelete="SET NULL"),sa.ForeignKeyConstraint(["unit_id"],["product_units.id"],ondelete="RESTRICT"),sa.UniqueConstraint("tenant_id","sku",name="uq_products_tenant_sku"))
    op.create_index("ix_products_tenant_id","products",["tenant_id"]);op.create_index("ix_products_category_id","products",["category_id"]);op.create_index("ix_products_unit_id","products",["unit_id"]);op.create_index("ix_products_name","products",["name"]);op.create_index("ix_products_barcode","products",["barcode"]);op.create_index("ix_products_is_active","products",["is_active"])

def downgrade():
    for i,t in [("ix_products_is_active","products"),("ix_products_barcode","products"),("ix_products_name","products"),("ix_products_unit_id","products"),("ix_products_category_id","products"),("ix_products_tenant_id","products")]: op.drop_index(i,table_name=t)
    op.drop_table("products")
    op.drop_index("ix_product_units_tenant_id",table_name="product_units");op.drop_table("product_units")
    op.drop_index("ix_product_categories_tenant_id",table_name="product_categories");op.drop_table("product_categories")
    for i,t in [("ix_customers_is_active","customers"),("ix_customers_name","customers"),("ix_customers_tenant_id","customers")]: op.drop_index(i,table_name=t)
    op.drop_table("customers")
