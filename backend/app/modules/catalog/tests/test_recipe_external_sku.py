from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_recipe_external_sku_is_company_scoped_and_active_lookup_exists():
    model = (ROOT / "modules/catalog/models.py").read_text(encoding="utf-8")
    service = (ROOT / "modules/catalog/service.py").read_text(encoding="utf-8")
    router = (ROOT / "modules/catalog/router.py").read_text(encoding="utf-8")
    assert "external_sku = Column(String(160), nullable=True, index=True)" in model
    assert "def get_recipe_by_external_sku" in service
    assert "Recipe.company_id == company_id" in service
    assert "Recipe.external_sku == value" in service
    assert "Recipe.is_active.is_(True)" in service
    assert '"/recipes/by-external-sku"' in router


def test_salla_mapping_binds_external_sku_to_recipe_without_replacing_internal_code():
    service = (ROOT / "modules/integrations/salla_product_mapping_service.py").read_text(encoding="utf-8")
    assert "recipe.external_sku = salla_sku" in service
    assert "Recipe.code remains the ERP-internal code" in service
    assert "CatalogProduct.company_id == company_id" in service
    assert "CatalogProduct.item_id == local_product.id" in service


def test_recipe_supports_multi_component_uom_and_cycle_controls():
    service = (ROOT / "modules/catalog/service.py").read_text(encoding="utf-8")
    schemas = (ROOT / "modules/catalog/schemas.py").read_text(encoding="utf-8")
    assert "Duplicate ingredient products are not allowed in one recipe" in service
    assert "Recipe would create an indirect product recipe cycle" in service
    assert "_recipe_line_conversion" in service
    assert "conversion_factor_to_product_uom=factor" in service
    assert "lines: list[RecipeLineCreate]" in schemas
    assert "uom_id: Optional[int]" in schemas
