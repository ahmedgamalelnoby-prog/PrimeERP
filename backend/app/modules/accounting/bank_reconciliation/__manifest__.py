from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/bank_reconciliation",
    display_name="Bank Reconciliation",
    version="1.0.0",
    domain="accounting",
    dependencies=("accounting/journal_entries",),
    permissions=("accounting.bank_reconciliation.read", "accounting.bank_reconciliation.write", "accounting.bank_reconciliation.post"),
    routes=("/accounting/bank-reconciliation",),
    menus=("Accounting", "Bank Reconciliation"),
    metadata={"migration_status": "canonical_boundary"},
)
