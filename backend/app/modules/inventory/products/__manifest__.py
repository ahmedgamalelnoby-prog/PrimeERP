from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="inventory/products",
    display_name="Products",
    version="1.0.0",
    domain="inventory",
    dependencies=("inventory/inventory_core",),
)
