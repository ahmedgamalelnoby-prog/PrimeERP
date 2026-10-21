from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="platform/subscriptions",
    display_name="Subscriptions",
    version="1.0.0",
    domain="platform",
    dependencies=("platform/plans",),
    permissions=(
        "platform.subscriptions.read",
        "platform.subscriptions.write",
        "platform.subscriptions.admin",
    ),
    routes=("/subscriptions",),
    menus=("Platform", "Subscriptions"),
    metadata={"migration_status": "canonical_service_api"},
)
