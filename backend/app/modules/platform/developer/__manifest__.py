from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="platform/developer",
    display_name="Developer Platform",
    version="1.0.0",
    domain="platform",
    dependencies=("core/identity",),
)
