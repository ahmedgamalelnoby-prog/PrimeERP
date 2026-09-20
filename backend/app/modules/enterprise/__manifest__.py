from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="enterprise/operations",
    display_name="Enterprise Operations",
    version="1.0.0",
    domain="enterprise",
    dependencies=("accounting/accounting_core", "accounting/chart_of_accounts", "accounting/journal_entries"),
    permissions=("enterprise.access", "enterprise.write", "enterprise.post"),
    routes=("/enterprise",),
)
