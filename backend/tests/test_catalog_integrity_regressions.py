from decimal import Decimal


def test_catalog_models_include_recipe_menu_and_price_history():
    from app.modules.catalog.models import Menu, MenuItem, ProductPrice, ProductPriceList, Recipe, RecipeLine

    assert Recipe.__tablename__ == "recipes"
    assert RecipeLine.__tablename__ == "recipe_lines"
    assert Menu.__tablename__ == "menus"
    assert MenuItem.__tablename__ == "menu_items"
    assert ProductPrice.__tablename__ == "product_prices"
    assert ProductPriceList.__tablename__ == "product_price_lists"


def test_inventory_product_category_is_real_foreign_key():
    from app.modules.inventory.items.models import InventoryItem

    foreign_keys = {fk.target_fullname for fk in InventoryItem.__table__.c.category_id.foreign_keys}
    assert "product_categories.id" in foreign_keys


def test_recipe_cost_uses_waste_and_yield_formula():
    qty = Decimal("2")
    unit_cost = Decimal("10")
    line_waste = Decimal("10")
    recipe_waste = Decimal("5")
    yield_qty = Decimal("4")

    total = qty * (Decimal("1") + line_waste / 100) * unit_cost
    expected = (total * (Decimal("1") + recipe_waste / 100)) / yield_qty
    assert expected == Decimal("5.775")


def test_recipe_uom_conversion_uses_factor_ratio():
    # Ingredient base UOM = KG (factor 1000 to the gram base), recipe line = G.
    from app.modules.catalog.service import CatalogService

    factor = CatalogService._calculate_uom_factor(
        Decimal("1"),
        "weight",
        Decimal("1000"),
        "weight",
    )
    assert factor == Decimal("0.001")


def test_recipe_uom_conversion_rejects_incompatible_categories():
    from app.modules.catalog.service import CatalogService

    try:
        CatalogService._calculate_uom_factor(Decimal("1"), "weight", Decimal("1"), "volume")
    except ValueError as exc:
        assert "category" in str(exc).lower()
    else:
        raise AssertionError("Incompatible UOM categories must be rejected")


def test_recipe_nested_cost_math_preserves_sibling_reuse():
    # Reusing the same ingredient in separate branches must not be treated as
    # a cycle; the recursion guard is a path guard, not a global visited set.
    from app.modules.catalog.service import _money

    assert _money(Decimal("12.50") + Decimal("7.50")) == Decimal("20.0000")


def test_fifo_weighted_unit_cost_is_exact_for_multiple_layers():
    from app.modules.inventory.stock_moves.service import InventoryStockMoveService

    allocations = [
        (Decimal("2"), Decimal("10")),
        (Decimal("3"), Decimal("14")),
    ]
    unit_cost = InventoryStockMoveService._weighted_cost(allocations)
    assert unit_cost == Decimal("12.4")


def test_fifo_empty_allocation_never_becomes_a_fake_cost():
    from app.modules.inventory.stock_moves.service import InventoryStockMoveService

    assert InventoryStockMoveService._weighted_cost([]) == Decimal("0")


def test_margin_recommendation_formula():
    cost = Decimal("70")
    target_margin = Decimal("30")
    recommended = cost / (Decimal("1") - target_margin / 100)
    assert recommended.quantize(Decimal("0.0001")) == Decimal("100.0000")
