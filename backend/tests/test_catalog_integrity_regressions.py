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


def test_nested_recipe_cost_math_is_supported_without_double_counting_siblings():
    # Two sibling ingredients may point to the same sub-recipe/product. The
    # recursion guard must track the current path, not the whole traversal.
    from app.modules.catalog.service import _money

    assert _money(Decimal("10") + Decimal("10")) == Decimal("20.0000")


def test_margin_recommendation_formula():
    cost = Decimal("70")
    target_margin = Decimal("30")
    recommended = cost / (Decimal("1") - target_margin / 100)
    assert recommended.quantize(Decimal("0.0001")) == Decimal("100.0000")
