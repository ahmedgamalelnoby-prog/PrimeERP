from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="contracts/legal",
    display_name="Legal",
    version="1.0.0",
    domain="contracts",
    metadata={"migration_status": "legacy-compatibility"},
)
