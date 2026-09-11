"""Manifest for the Accounting Journal Entries add-on."""

from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/journal_entries",
    display_name="Journal Entries",
    version="1.0.1",
    domain="accounting",
    dependencies=("accounting/accounting_core", "accounting/chart_of_accounts"),
    permissions=frozenset(
        {
            "accounting.journal_entries.read",
            "accounting.journal_entries.write",
            "accounting.journal_entries.post",
        }
    ),
    routes=("/accounting/journal-entries",),
    menus=("Accounting", "Journal Entries"),
    metadata={
        "migration_status": "canonical_boundary",
        "legacy_path": "app.modules.accounting.journal_entries",
    },
)
