from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/assets",
    display_name="Fixed Assets",
    version="1.0.0",
    domain="accounting",
    dependencies=("accounting/journal_entries", "accounting/chart_of_accounts"),
    permissions=("accounting.assets.read", "accounting.assets.write", "accounting.assets.post"),
    routes=("/accounting/assets",),
    menus=("Accounting", "Fixed Assets"),
    metadata={"migration_status": "canonical_boundary"},
)
