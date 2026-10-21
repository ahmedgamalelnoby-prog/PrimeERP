from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="sales/sales_orders",
    display_name="Sales Orders",
    version="1.0.0",
    domain="sales",
    dependencies=("sales/sales_core", "sales/quotations"),
)
