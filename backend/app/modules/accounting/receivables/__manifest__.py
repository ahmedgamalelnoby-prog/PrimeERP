from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/receivables",
    display_name="Accounts Receivable",
    version="1.0.0",
    domain="accounting",
    dependencies=("accounting/journal_entries", "accounting/taxes"),
    permissions=("accounting.receivables.read", "accounting.receivables.write", "accounting.receivables.collect"),
    routes=("/accounting/receivables",),
    menus=("Accounting", "Accounts Receivable"),
    metadata={"migration_status": "canonical_service_api"},
)
