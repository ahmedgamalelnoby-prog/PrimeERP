from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/journal_entries",
    display_name="Journal Entries",
    version="1.0.0",
    domain="accounting",
    dependencies=("accounting/accounting_core", "accounting/chart_of_accounts"),
)
