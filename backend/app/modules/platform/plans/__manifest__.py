from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="platform/plans",
    display_name="Plans",
    version="1.0.0",
    domain="platform",
    permissions=(
        "platform.plans.read",
        "platform.plans.write",
    ),
    routes=("/plans",),
    menus=("Platform", "Plans"),
    metadata={"migration_status": "canonical_service_api"},
)
