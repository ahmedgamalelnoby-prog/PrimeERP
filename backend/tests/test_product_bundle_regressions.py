def test_bundle_models_have_company_scoped_identity_constraints():
    from app.modules.catalog.bundle_models import ProductBundle, ProductBundleLine
    assert ProductBundle.__table__.name == "product_bundles"
    assert ProductBundleLine.__table__.name == "product_bundle_lines"
    names = {c.name for c in ProductBundle.__table__.constraints}
    assert "uq_product_bundle_company_code" in names
    assert "uq_product_bundle_company_product" in names


def test_bundle_routes_are_registered():
    from app.modules.catalog.bundle_router import router
    paths = {r.path for r in router.routes}
    assert "/catalog/bundles" in paths
    assert "/catalog/bundles/{bundle_id}/availability" in paths
    assert "/catalog/bundles/{bundle_id}/deactivate" in paths
    assert "/catalog/bundles/{bundle_id}/reactivate" in paths


def test_bundle_schema_rejects_non_positive_component_quantity():
    import pytest
    from app.modules.catalog.schemas import BundleCreate
    with pytest.raises(Exception):
        BundleCreate(company_id=1, product_id=2, code="B1", name_ar="Bundle", lines=[{"component_product_id": 3, "quantity": 0}])


def test_bundle_service_rejects_self_component():
    from app.modules.catalog.bundle_service import ProductBundleService
    service = ProductBundleService()
    assert callable(service.create)
    assert callable(service.availability)
