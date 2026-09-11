from app.core.module_engine.manifest import manifest


MANIFEST = manifest(
    technical_name="inventory/costing",
    display_name="Inventory Costing",
    version="1.0.0",
    domain="inventory",
    dependencies=("inventory/stock_moves",),
    permissions=("inventory.costing.read",),
    routes=("/inventory/costing",),
    menus=("Inventory", "Costing"),
    metadata={
        "migration_status": "canonical_service_api",
        "costing_method": "weighted_average",
    },
)
