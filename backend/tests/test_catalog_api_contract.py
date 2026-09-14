def test_catalog_router_exposes_complete_product_lifecycle():
    from app.modules.catalog.router import router

    paths = {route.path for route in router.routes}
    expected = {
        "/catalog/categories",
        "/catalog/price-lists",
        "/catalog/prices",
        "/catalog/products/{product_id}/base-price",
        "/catalog/products/{product_id}/cost-history",
        "/catalog/products/{product_id}/pricing-analysis",
        "/catalog/recipes",
        "/catalog/recipes/{recipe_id}",
        "/catalog/menus",
        "/catalog/menus/{menu_id}",
        "/catalog/menus/{menu_id}/items",
    }
    assert expected.issubset(paths)
