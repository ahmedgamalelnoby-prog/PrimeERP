from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="sales/quotations",
    display_name="Sales Quotations",
    version="1.0.0",
    domain="sales",
    dependencies=("sales/sales_core",),
)
