from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/vat",
    display_name="VAT",
    version="1.0.0",
    domain="accounting",
    dependencies=("accounting/taxes",),
    permissions=("accounting.vat.read", "accounting.vat.write"),
    routes=("/accounting/vat",),
    menus=("Accounting", "VAT"),
    metadata={"migration_status": "canonical_service_api"},
)
