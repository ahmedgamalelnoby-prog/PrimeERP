from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _source():
    return (ROOT / "app/modules/integrations/salla_erp_service.py").read_text(encoding="utf-8")


def test_salla_execution_imports_typed_product_mapping():
    source = _source()
    assert "IntegrationProductMapping" in source
    assert "def _typed_product_mapping" in source
    assert "IntegrationProductMapping.company_id == order.company_id" in source
    assert "IntegrationProductMapping.connection_id == order.connection_id" in source
    assert "sync_status.in_([\"active\", \"paused\"])" in source


def test_salla_execution_validates_mapped_product_and_variant_tenant():
    source = _source()
    assert "InventoryItem.company_id == order.company_id" in source
    assert "ProductVariant.company_id == order.company_id" in source
    assert "ProductVariant.product_id == product.id" in source
    assert "ProductVariant.is_active.is_(True)" in source


def test_salla_order_keeps_legacy_mapping_only_as_fallback():
    source = _source()
    typed = source.index("typed_product, typed_variant = _typed_product_mapping")
    legacy = source.index('mapped = _mapping(db, order.company_id, order.connection_id, "salla_product", external)')
    assert typed < legacy


def test_salla_sales_line_persists_typed_variant():
    source = _source()
    assert "product, variant = _product(db, order, s_item)" in source
    assert "variant_id=variant.id if variant else None" in source


def test_salla_reversal_preserves_variant():
    source = _source()
    assert "SalesLine(item_id=line.item_id, variant_id=line.variant_id" in source


def test_salla_product_lookup_is_company_scoped():
    source = _source()
    assert "SallaProduct.company_id == order.company_id" in source
