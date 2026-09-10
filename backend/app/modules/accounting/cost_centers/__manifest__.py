from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/cost_centers",
    display_name="Cost Centers",
    version="1.0.0",
    domain="accounting",
    dependencies=("accounting/accounting_core", "accounting/chart_of_accounts"),
    permissions=("accounting.cost_centers.read", "accounting.cost_centers.write"),
    routes=("/accounting/cost-centers",),
    menus=("Accounting", "Cost Centers"),
    metadata={"migration_status": "canonical_boundary"},
)
