from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mapping_model_and_migration_exist():
    model = (ROOT / "app/modules/integrations/models.py").read_text(encoding="utf-8")
    migration = (ROOT / "alembic/versions/20260914_integration_product_mappings.py").read_text(encoding="utf-8")
    assert "class IntegrationProductMapping" in model
    assert "uq_integration_product_mapping_external" in model
    assert "uq_integration_product_mapping_local" in model
    assert "20260914_product_bundles" in migration
    assert "product_variants" in migration
    assert "sync_direction IN ('inbound','outbound','bidirectional')" in migration


def test_mapping_service_enforces_company_and_variant_relationship():
    service = (ROOT / "app/modules/integrations/product_mapping_service.py").read_text(encoding="utf-8")
    assert "IntegrationConnection.company_id == company_id" in service
    assert "InventoryItem.company_id == company_id" in service
    assert "ProductVariant.company_id == company_id" in service
    assert "ProductVariant.product_id == product_id" in service
    assert "with_for_update()" in service


def test_mapping_router_requires_integration_access_and_write():
    router = (ROOT / "app/modules/integrations/product_mapping_router.py").read_text(encoding="utf-8")
    assert 'require_permission("integrations.access")' in router
    assert 'require_permission("integrations.write")' in router
    assert 'require_module("integrations")' in router
    assert 'router = APIRouter(prefix="/integrations/product-mappings"' in router


def test_api_router_registers_mapping_router():
    router = (ROOT / "app/api/v1/router.py").read_text(encoding="utf-8")
    assert "integration_product_mapping_router" in router
    assert "api_router.include_router(integration_product_mapping_router)" in router
