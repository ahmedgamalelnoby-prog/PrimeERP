from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/withholding_tax",
    display_name="Withholding Tax",
    version="1.0.0",
    domain="accounting",
    dependencies=("accounting/accounting_core",),
    permissions=("accounting.withholding_tax.read", "accounting.withholding_tax.write"),
    routes=("/accounting/withholding-tax",),
    menus=("Accounting", "Withholding Tax"),
    metadata={"migration_status": "canonical_service_api"},
)
