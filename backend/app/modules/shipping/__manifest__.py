from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name='logistics/shipping',
    display_name='Shipping & Logistics',
    version='1.0.0',
    domain='logistics',
    dependencies=('commerce/sales_purchasing', 'inventory/inventory_core'),
)
