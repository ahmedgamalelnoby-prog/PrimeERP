from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/payables",
    display_name="Accounts Payable",
    version="1.0.0",
    domain="accounting",
    dependencies=("accounting/journal_entries", "accounting/taxes"),
    permissions=("accounting.payables.read", "accounting.payables.write", "accounting.payables.pay"),
    routes=("/accounting/payables",),
    menus=("Accounting", "Accounts Payable"),
    metadata={"migration_status": "canonical_service_api"},
)
