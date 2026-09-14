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
        "/catalog/pricing-impact",
        "/catalog/recipes",
        "/catalog/recipes/{recipe_id}",
        "/catalog/menus",
        "/catalog/menus/{menu_id}",
        "/catalog/menus/{menu_id}/items",
    }
    assert expected.issubset(paths)


def test_catalog_router_requires_tenant_scoped_company_resolution():
    from app.modules.catalog.router import _company_for_user

    assert _company_for_user.__annotations__.get("user") is not None


def test_pricing_analysis_supports_channel_price_list():
    from app.modules.catalog.router import router
    from app.modules.catalog.schemas import PricingAnalysis

    route = next(r for r in router.routes if r.path == "/catalog/products/{product_id}/pricing-analysis")
    parameter_names = {p.name for p in route.dependant.query_params}
    assert "price_list_id" in parameter_names
    assert "target_margin" in parameter_names
    assert "price_list_id" in PricingAnalysis.model_fields


def test_pricing_impact_contract():
    from app.modules.catalog.router import router
    from app.modules.catalog.schemas import PricingImpactResponse

    route = next(r for r in router.routes if r.path == "/catalog/pricing-impact")
    parameter_names = {p.name for p in route.dependant.query_params}
    assert {"company_id", "price_list_id", "target_margin", "below_margin"}.issubset(parameter_names)
    assert {"target_margin", "below_margin", "price_list_id", "count", "items"}.issubset(PricingImpactResponse.model_fields)
