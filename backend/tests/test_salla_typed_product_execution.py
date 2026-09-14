from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_salla_execution_imports_typed_product_mapping():
    source = (ROOT / "app/modules/integrations/salla_erp_service.py").read_text(encoding="utf-8")
    assert "IntegrationProductMapping" in source
    assert "def _typed_product_mapping" in source
    assert "IntegrationProductMapping.company_id == order.company_id" in source
    assert "IntegrationProductMapping.connection_id == order.connection_id" in source
    assert "sync_status.in_([\"active\", \"paused\"])" in source


def test_salla_execution_validates_mapped_product_and_variant_tenant():
    source = (ROOT / "app/modules/integrations/salla_erp_service.py").read_text(encoding="utf-8")
    assert "InventoryItem.company_id == order.company_id" in source
    assert "ProductVariant.company_id == order.company_id" in source
    assert "ProductVariant.product_id == product.id" in source
    assert "ProductVariant.is_active.is_(True)" in source


def test_salla_order_keeps_legacy_mapping_only_as_fallback():
    source = (ROOT / "app/modules/integrations/salla_erp_service.py").read_text(encoding="utf-8")
    typed = source.index("typed_product = _typed_product_mapping")
    legacy = source.index('mapped = _mapping(db, order.company_id, order.connection_id, "salla_product", external)')
    assert typed < legacy


def test_salla_product_lookup_is_company_scoped():
    source = (ROOT / "app/modules/integrations/salla_erp_service.py").read_text(encoding="utf-8")
    assert "SallaProduct.company_id == order.company_id" in source
