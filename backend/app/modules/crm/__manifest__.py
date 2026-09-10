from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="crm/crm_core",
    display_name="CRM Core",
    version="1.0.0",
    domain="crm",
    metadata={"migration_status": "legacy-compatibility"},
)
