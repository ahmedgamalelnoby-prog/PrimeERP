from app.core.module_engine.manifest import manifest
MANIFEST = manifest(
    technical_name='commerce',
    display_name='Sales & Purchasing',
    version='1.0.0',
    domain='commerce',
    dependencies=('inventory', 'accounting/accounting_core'),
)
