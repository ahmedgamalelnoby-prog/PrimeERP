from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="inventory/warehouses",
    display_name="Warehouses",
    version="1.0.0",
    domain="inventory",
    dependencies=("inventory/inventory_core",),
)
