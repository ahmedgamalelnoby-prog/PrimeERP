from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/budgets",
    display_name="Budgets",
    version="1.0.0",
    domain="accounting",
    dependencies=("accounting/accounting_core", "accounting/cost_centers"),
    permissions=("accounting.budgets.read", "accounting.budgets.write", "accounting.budgets.approve"),
    routes=("/accounting/budgets",),
    menus=("Accounting", "Budgets"),
    metadata={"migration_status": "canonical_boundary"},
)
