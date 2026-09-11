from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="purchasing/suppliers",
    display_name="Suppliers",
    version="1.0.0",
    domain="purchasing",
    dependencies=("organization/companies",),
    permissions=("purchasing.suppliers.read", "purchasing.suppliers.write"),
    routes=("/purchasing/suppliers",),
    menus=("Purchasing", "Suppliers"),
    metadata={"migration_status": "canonical_service_api"},
)
