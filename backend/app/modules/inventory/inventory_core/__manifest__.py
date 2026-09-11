from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="inventory/inventory_core",
    display_name="Inventory Core",
    version="1.1.0",
    domain="inventory",
    dependencies=(),
    permissions=(
        "inventory.items.read",
        "inventory.items.write",
        "inventory.stock.read",
        "inventory.stock.write",
    ),
    routes=("/inventory", "/inventory/items"),
    menus=("Inventory", "Items", "Stock"),
    metadata={
        "migration_status": "canonical_item_boundary",
        "business_capabilities": (
            "item_master",
            "sku_barcode",
            "stock_balance",
            "costing",
        ),
    },
)
