from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="finance/installments",
    display_name="Installments",
    version="1.0.0",
    domain="finance",
    metadata={"migration_status": "legacy-compatibility"},
)
