from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="core/dashboard",
    display_name="Dashboard",
    version="1.0.0",
    domain="core",
    metadata={"migration_status": "legacy-compatibility", "presentation_layer": "true"},
)
