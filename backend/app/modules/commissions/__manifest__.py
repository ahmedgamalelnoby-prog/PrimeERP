from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="sales/commissions",
    display_name="Sales Commissions",
    version="1.0.0",
    domain="sales",
    dependencies=("sales/sales_core",),
    metadata={"migration_status": "legacy-compatibility"},
)
