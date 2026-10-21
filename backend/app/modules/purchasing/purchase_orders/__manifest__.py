from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="purchasing/purchase_orders",
    display_name="Purchase Orders",
    version="1.0.0",
    domain="purchasing",
    dependencies=("purchasing/suppliers", "inventory/inventory_core", "inventory/warehouses"),
    permissions=("purchasing.purchase_orders.read", "purchasing.purchase_orders.write", "purchasing.purchase_orders.approve"),
    routes=("/purchasing/purchase-orders",),
    menus=("Purchasing", "Purchase Orders"),
    metadata={"migration_status": "canonical_service_api", "business_capabilities": ("purchase_order", "supplier_procurement", "receipt_tracking")},
)
