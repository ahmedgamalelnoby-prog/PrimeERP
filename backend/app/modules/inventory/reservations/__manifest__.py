from app.core.module_engine.manifest import manifest


MANIFEST = manifest(
    technical_name="inventory/reservations",
    display_name="Inventory Reservations",
    version="1.0.0",
    domain="inventory",
    dependencies=("inventory/inventory_core", "inventory/locations", "inventory/stock_moves"),
    permissions=(
        "inventory.reservations.read",
        "inventory.reservations.write",
        "inventory.reservations.release",
        "inventory.reservations.consume",
    ),
    routes=("/inventory/reservations",),
    menus=("Inventory", "Reservations"),
    metadata={
        "migration_status": "canonical_service_api",
        "business_capabilities": ("available_stock", "reservation_lifecycle", "order_allocation"),
    },
)
