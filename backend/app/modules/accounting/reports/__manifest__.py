from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/reports",
    display_name="Financial Reports",
    version="1.0.0",
    domain="accounting",
    dependencies=("accounting/journal_entries", "accounting/chart_of_accounts"),
    permissions=("accounting.reports.read",),
    routes=("/accounting/reports",),
    menus=("Accounting", "Financial Reports"),
    metadata={"migration_status": "canonical_boundary"},
)
