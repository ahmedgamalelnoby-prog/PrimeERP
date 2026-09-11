from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="people/hr_core",
    display_name="HR Core",
    version="1.0.0",
    domain="people",
    metadata={"migration_status": "legacy-compatibility"},
)
