from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/chart_of_accounts",
    display_name="Chart of Accounts",
    version="1.0.1",
    domain="accounting",
    dependencies=("accounting/accounting_core",),
    permissions=frozenset(
        {
            "accounting.chart_of_accounts.read",
            "accounting.chart_of_accounts.write",
        }
    ),
    routes=("/chart-of-accounts",),
    menus=("Accounting", "Chart of Accounts"),
    metadata={"migration_status": "canonical_service_api"},
)
