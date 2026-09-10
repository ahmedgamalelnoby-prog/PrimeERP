from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/chart_of_accounts",
    display_name="Chart of Accounts",
    version="1.0.0",
    domain="accounting",
    dependencies=("accounting/accounting_core",),
)
