from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="platform/customers",
    display_name="Customers",
    version="1.0.0",
    domain="platform",
    dependencies=("core/identity", "organization/companies"),
    permissions=("platform.customers.read", "platform.customers.write"),
    routes=("/customers",),
    menus=("Platform", "Customers"),
    metadata={"migration_status": "canonical_service_api", "business_capabilities": ("customer_master", "customer_credit_profile")},
)
