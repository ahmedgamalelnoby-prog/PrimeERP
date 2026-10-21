from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="organization/branches",
    display_name="Branches",
    version="1.0.0",
    domain="organization",
    dependencies=("organization/companies",),
    metadata={"migration_status": "legacy-compatibility"},
)
