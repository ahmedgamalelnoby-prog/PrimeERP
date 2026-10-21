from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="treasury/core",
    display_name="Treasury & Cash Management",
    version="1.0.0",
    domain="treasury",
    dependencies=("accounting/journal_entries", "platform/customers"),
    permissions=("treasury.read", "treasury.write", "treasury.collect", "treasury.reverse"),
    routes=("/treasury",),
    menus=("Finance", "Treasury"),
    metadata={"migration_status": "canonical_service_api"},
)
