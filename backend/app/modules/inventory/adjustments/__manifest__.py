from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="inventory/adjustments",
    display_name="Inventory Adjustments",
    version="1.0.0",
    domain="inventory",
    dependencies=("inventory/stock_moves",),
    permissions=(
        "inventory.adjustments.read",
        "inventory.adjustments.write",
        "inventory.adjustments.approve",
        "inventory.adjustments.post",
    ),
    routes=("/inventory/adjustments",),
    menus=("Inventory", "Adjustments"),
    metadata={"migration_status": "canonical_workflow_boundary"},
)
