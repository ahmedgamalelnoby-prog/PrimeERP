def test_variant_lifecycle_service_exists():
    from app.modules.catalog.variant_lifecycle_service import ProductVariantLifecycleService

    service = ProductVariantLifecycleService()
    assert callable(service.update_variant)
    assert callable(service.deactivate_variant)
    assert callable(service.reactivate_variant)
    assert callable(service.deactivate_barcode)
    assert callable(service.reactivate_barcode)


def test_variant_routes_expose_lifecycle_operations():
    from app.modules.catalog.variant_router import router

    paths = {route.path for route in router.routes}
    assert "/catalog/variants/{variant_id}" in paths
    assert "/catalog/variants/{variant_id}/deactivate" in paths
    assert "/catalog/variants/{variant_id}/reactivate" in paths
    assert "/catalog/barcodes/{barcode_id}/deactivate" in paths
    assert "/catalog/barcodes/{barcode_id}/reactivate" in paths


def test_variant_migration_uses_company_scoped_sku_and_primary_barcode_constraints():
    from pathlib import Path

    migration = Path(__file__).parents[1] / "alembic" / "versions" / "20260914_product_variants.py"
    text = migration.read_text(encoding="utf-8")
    assert "uq_product_variant_company_sku" in text
    assert "ux_product_primary_barcode" in text
    assert "company_id", "product_id" in text
