from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="inventory/warehouses",
    display_name="Warehouses",
    version="1.0.1",
    domain="inventory",
    dependencies=("inventory/inventory_core",),
    permissions=(
        "inventory.warehouses.read",
        "inventory.warehouses.write",
    ),
    routes=("/inventory/warehouses",),
    menus=("Inventory", "Warehouses"),
    metadata={"migration_status": "canonical_service_api"},
)
