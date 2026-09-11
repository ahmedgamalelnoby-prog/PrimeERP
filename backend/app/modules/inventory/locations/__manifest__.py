from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="inventory/locations",
    display_name="Locations",
    version="1.0.0",
    domain="inventory",
    dependencies=("inventory/warehouses",),
    permissions=(
        "inventory.locations.read",
        "inventory.locations.write",
    ),
    routes=("/inventory/locations",),
    menus=("Inventory", "Locations"),
    metadata={"migration_status": "canonical_service_api"},
)
