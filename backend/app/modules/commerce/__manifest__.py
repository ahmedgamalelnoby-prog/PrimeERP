from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="commerce/sales_purchasing",
    display_name="Sales & Purchasing",
    version="1.0.0",
    domain="commerce",
    dependencies=("inventory/inventory_core", "accounting/accounting_core"),
)
