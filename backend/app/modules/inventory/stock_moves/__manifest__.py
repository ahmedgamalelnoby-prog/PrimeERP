from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="inventory/stock_moves",
    display_name="Stock Moves",
    version="1.0.3",
    domain="inventory",
    dependencies=("inventory/inventory_core", "inventory/locations"),
    permissions=(
        "inventory.stock_moves.read",
        "inventory.stock_moves.write",
        "inventory.stock_moves.post",
    ),
    routes=("/inventory/stock-moves",),
    menus=("Inventory", "Stock Moves"),
    metadata={"migration_status": "canonical_ledger_boundary"},
)
