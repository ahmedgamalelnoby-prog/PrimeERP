from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/journal_items",
    display_name="Journal Items",
    version="1.0.0",
    domain="accounting",
    dependencies=("accounting/journal_entries",),
    permissions=("accounting.journal_items.read",),
    routes=("/accounting/journal-items",),
    menus=("Accounting", "Journal Items"),
    metadata={"migration_status": "shared_model_boundary"},
)
