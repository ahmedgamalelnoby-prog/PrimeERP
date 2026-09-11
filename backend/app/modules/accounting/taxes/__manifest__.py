from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/taxes",
    display_name="Taxes",
    version="1.0.0",
    domain="accounting",
    dependencies=("accounting/accounting_core",),
    permissions=("accounting.taxes.read", "accounting.taxes.write"),
    routes=("/accounting/taxes",),
    menus=("Accounting", "Taxes"),
    metadata={"migration_status": "canonical_service_api"},
)
