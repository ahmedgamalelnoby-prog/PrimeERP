from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="organization/companies",
    display_name="Companies",
    version="1.0.0",
    domain="organization",
    metadata={"migration_status": "legacy-compatibility"},
)
