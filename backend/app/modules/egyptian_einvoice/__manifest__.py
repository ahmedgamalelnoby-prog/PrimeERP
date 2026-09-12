from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="localization/egyptian_einvoice",
    display_name="Egyptian E-Invoicing",
    version="1.1.0",
    domain="localization",
    dependencies=("accounting/accounting_core",),
    permissions=frozenset({"einvoice.access", "einvoice.write", "einvoice.post"}),
    routes=("/egyptian-einvoice",),
    metadata={"migration_status": "production-integration-foundation", "country": "EG", "eta_api": "v1.0"},
)
