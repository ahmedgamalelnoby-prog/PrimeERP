from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="localization/egyptian_einvoice",
    display_name="Egyptian E-Invoicing",
    version="1.0.0",
    domain="localization",
    dependencies=("accounting/accounting_core",),
    metadata={"migration_status": "legacy-compatibility", "country": "EG"},
)
