from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="sales/sales_core",
    display_name="Sales Core",
    version="1.1.0",
    domain="sales",
    dependencies=("organization/companies", "platform/customers", "inventory/warehouses"),
    permissions=("sales.orders.read", "sales.orders.write", "sales.orders.confirm"),
    routes=("/sales/orders",),
    menus=("Sales", "Orders"),
    metadata={"migration_status": "canonical_service_api", "business_capabilities": ("customer_sales", "sales_order")},
)
