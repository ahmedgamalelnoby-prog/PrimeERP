from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="inventory/transfers",
    display_name="Inventory Transfers",
    version="1.0.0",
    domain="inventory",
    dependencies=("inventory/stock_moves",),
    permissions=(
        "inventory.transfers.read",
        "inventory.transfers.write",
        "inventory.transfers.approve",
        "inventory.transfers.post",
    ),
    routes=("/inventory/transfers",),
    menus=("Inventory", "Transfers"),
    metadata={"migration_status": "canonical_workflow_boundary"},
)
