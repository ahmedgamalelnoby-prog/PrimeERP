"""Manifest for the Fiscal Periods add-on."""

from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="accounting/fiscal_periods",
    display_name="Fiscal Periods",
    version="1.0.1",
    domain="accounting",
    dependencies=("accounting/accounting_core",),
    permissions=frozenset(
        {
            "accounting.fiscal_periods.read",
            "accounting.fiscal_periods.write",
            "accounting.fiscal_periods.close",
        }
    ),
    routes=("/accounting/fiscal-periods",),
    menus=("Accounting", "Fiscal Periods"),
    metadata={
        "migration_status": "canonical_boundary",
        "legacy_path": "app.modules.accounting.fiscal_years",
    },
)
