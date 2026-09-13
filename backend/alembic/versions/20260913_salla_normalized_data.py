"""Persist normalized Salla commerce/catalog data.

Revision ID: 20260913_salla_normalized_data
Revises: 20260913_product_tax_profiles
"""

from alembic import op
import sqlalchemy as sa

revision = "20260913_salla_normalized_data"
down_revision = "20260913_product_tax_profiles"
branch_labels = None
depends_on = None


def _common(table):
    return [
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("connection_id", sa.Integer(), sa.ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.String(160), nullable=False),
    ]


def upgrade():
    op.create_table("salla_orders", *_common("salla_orders"),
        sa.Column("reference_id", sa.String(160)), sa.Column("status", sa.String(80)),
        sa.Column("payment_status", sa.String(80)), sa.Column("fulfillment_status", sa.String(80)),
        sa.Column("order_type", sa.String(80)), sa.Column("currency", sa.String(20)),
        sa.Column("exchange_rate", sa.Numeric(20, 8)), sa.Column("subtotal", sa.Numeric(20, 4)),
        sa.Column("discount", sa.Numeric(20, 4)), sa.Column("shipping", sa.Numeric(20, 4)),
        sa.Column("tax", sa.Numeric(20, 4)), sa.Column("total", sa.Numeric(20, 4)),
        sa.Column("cod_amount", sa.Numeric(20, 4)), sa.Column("customer_id", sa.String(160)),
        sa.Column("store_id", sa.String(160)), sa.Column("created_at_salla", sa.DateTime(timezone=True)),
        sa.Column("updated_at_salla", sa.DateTime(timezone=True)), sa.Column("urls", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("payment_methods", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("connection_id", "external_id", name="uq_salla_order_connection_external"))

    op.create_table("salla_order_items", *_common("salla_order_items"),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("salla_orders.id", ondelete="CASCADE")),
        sa.Column("product_external_id", sa.String(160)), sa.Column("variant_external_id", sa.String(160)),
        sa.Column("sku", sa.String(160)), sa.Column("name", sa.String(500)), sa.Column("quantity", sa.Numeric(20, 6)),
        sa.Column("price", sa.Numeric(20, 4)), sa.Column("subtotal", sa.Numeric(20, 4)), sa.Column("discount", sa.Numeric(20, 4)),
        sa.Column("tax", sa.Numeric(20, 4)), sa.Column("total", sa.Numeric(20, 4)), sa.Column("cost_price", sa.Numeric(20, 4)),
        sa.Column("currency", sa.String(20)), sa.Column("options", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("taxes", sa.JSON(), nullable=False, server_default="[]"), sa.Column("codes", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("urls", sa.JSON(), nullable=False, server_default="{}"), sa.Column("raw_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("connection_id", "external_id", name="uq_salla_order_item_connection_external"))

    op.create_table("salla_customers", *_common("salla_customers"),
        sa.Column("first_name", sa.String(160)), sa.Column("last_name", sa.String(160)), sa.Column("mobile", sa.String(80)),
        sa.Column("mobile_code", sa.String(20)), sa.Column("email", sa.String(320)), sa.Column("gender", sa.String(30)),
        sa.Column("city", sa.String(160)), sa.Column("country", sa.String(160)), sa.Column("country_code", sa.String(20)),
        sa.Column("location", sa.JSON(), nullable=False, server_default="{}"), sa.Column("urls", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("groups", sa.JSON(), nullable=False, server_default="[]"), sa.Column("updated_at_salla", sa.DateTime(timezone=True)),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default="{}"), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("connection_id", "external_id", name="uq_salla_customer_connection_external"))

    op.create_table("salla_products", *_common("salla_products"),
        sa.Column("sku", sa.String(160)), sa.Column("mpn", sa.String(160)), sa.Column("gtin", sa.String(160)), sa.Column("product_type", sa.String(80)),
        sa.Column("name", sa.String(500)), sa.Column("status", sa.String(80)), sa.Column("price", sa.Numeric(20, 4)),
        sa.Column("taxed_price", sa.Numeric(20, 4)), sa.Column("pre_tax_price", sa.Numeric(20, 4)), sa.Column("tax", sa.Numeric(20, 4)),
        sa.Column("sale_price", sa.Numeric(20, 4)), sa.Column("cost_price", sa.Numeric(20, 4)), sa.Column("quantity", sa.Numeric(20, 6)),
        sa.Column("weight", sa.Numeric(20, 6)), sa.Column("weight_type", sa.String(30)), sa.Column("weight_unit", sa.String(30)),
        sa.Column("currency", sa.String(20)), sa.Column("require_shipping", sa.Boolean()), sa.Column("is_available", sa.Boolean()),
        sa.Column("unlimited_quantity", sa.Boolean()), sa.Column("sold_quantity", sa.Numeric(20, 6)), sa.Column("regular_price", sa.Numeric(20, 4)),
        sa.Column("maximum_quantity_per_order", sa.Numeric(20, 6)), sa.Column("max_items_per_user", sa.Numeric(20, 6)), sa.Column("notify_quantity", sa.Numeric(20, 6)),
        sa.Column("category_ids", sa.JSON(), nullable=False, server_default="[]"), sa.Column("brand", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("channels", sa.JSON(), nullable=False, server_default="[]"), sa.Column("options", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"), sa.Column("urls", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("images", sa.JSON(), nullable=False, server_default="[]"), sa.Column("raw_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("updated_at_salla", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("connection_id", "external_id", name="uq_salla_product_connection_external"))

    op.create_table("salla_product_variants", *_common("salla_product_variants"),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("salla_products.id", ondelete="CASCADE")), sa.Column("sku", sa.String(160)),
        sa.Column("barcode", sa.String(160)), sa.Column("mpn", sa.String(160)), sa.Column("gtin", sa.String(160)),
        sa.Column("price", sa.Numeric(20, 4)), sa.Column("regular_price", sa.Numeric(20, 4)), sa.Column("cost_price", sa.Numeric(20, 4)),
        sa.Column("sale_price", sa.Numeric(20, 4)), sa.Column("stock", sa.Numeric(20, 6)), sa.Column("weight", sa.Numeric(20, 6)),
        sa.Column("weight_type", sa.String(30)), sa.Column("option_values", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default="{}"), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("connection_id", "external_id", name="uq_salla_variant_connection_external"))

    op.create_table("salla_shipments", *_common("salla_shipments"),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("salla_orders.id", ondelete="SET NULL")), sa.Column("order_external_id", sa.String(160)),
        sa.Column("order_reference_id", sa.String(160)), sa.Column("shipment_type", sa.String(80)), sa.Column("courier_id", sa.String(160)),
        sa.Column("courier_name", sa.String(240)), sa.Column("external_company_name", sa.String(240)), sa.Column("shipping_number", sa.String(160)),
        sa.Column("tracking_number", sa.String(160)), sa.Column("tracking_link", sa.String(1000)), sa.Column("label", sa.String(2000)),
        sa.Column("payment_method", sa.String(40)), sa.Column("source", sa.String(80)), sa.Column("status", sa.String(80)),
        sa.Column("total", sa.Numeric(20, 4)), sa.Column("cash_on_delivery", sa.Numeric(20, 4)), sa.Column("total_weight", sa.Numeric(20, 6)),
        sa.Column("international", sa.Boolean()), sa.Column("trackable", sa.Boolean()), sa.Column("packages", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("ship_from", sa.JSON(), nullable=False, server_default="{}"), sa.Column("ship_to", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("meta", sa.JSON(), nullable=False, server_default="{}"), sa.Column("billing_account", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at_salla", sa.DateTime(timezone=True)), sa.Column("raw_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("connection_id", "external_id", name="uq_salla_shipment_connection_external"))

    op.create_table("salla_invoices", *_common("salla_invoices"),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("salla_orders.id", ondelete="SET NULL")), sa.Column("invoice_number", sa.String(160)),
        sa.Column("status", sa.String(80)), sa.Column("subtotal", sa.Numeric(20, 4)), sa.Column("discount", sa.Numeric(20, 4)),
        sa.Column("tax", sa.Numeric(20, 4)), sa.Column("shipping", sa.Numeric(20, 4)), sa.Column("total", sa.Numeric(20, 4)),
        sa.Column("currency", sa.String(20)), sa.Column("issue_date", sa.Date()), sa.Column("due_date", sa.Date()),
        sa.Column("urls", sa.JSON(), nullable=False, server_default="{}"), sa.Column("raw_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("connection_id", "external_id", name="uq_salla_invoice_connection_external"))

    for table, columns in {
        "salla_orders": ["company_id", "connection_id", "reference_id", "customer_id"],
        "salla_order_items": ["company_id", "connection_id", "order_id", "product_external_id", "variant_external_id", "sku"],
        "salla_customers": ["company_id", "connection_id", "mobile", "email"],
        "salla_products": ["company_id", "connection_id", "sku", "gtin"],
        "salla_product_variants": ["company_id", "connection_id", "product_id", "sku", "barcode"],
        "salla_shipments": ["company_id", "connection_id", "order_id", "order_external_id", "order_reference_id", "shipping_number", "tracking_number", "status"],
        "salla_invoices": ["company_id", "connection_id", "order_id", "invoice_number"],
    }.items():
        for column in columns:
            op.create_index(f"ix_{table}_{column}", table, [column], unique=False)


def downgrade():
    for table in ["salla_invoices", "salla_shipments", "salla_product_variants", "salla_products", "salla_customers", "salla_order_items", "salla_orders"]:
        op.drop_table(table)
