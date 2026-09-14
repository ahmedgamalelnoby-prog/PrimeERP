from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_typed_mapping_model_has_explicit_entity_namespace():
    source = (ROOT / "app/modules/integrations/models.py").read_text(encoding="utf-8")
    assert 'entity_type = Column(String(20)' in source
    assert 'UniqueConstraint("connection_id", "entity_type", "external_id"' in source


def test_mapping_service_derives_entity_type_from_variant():
    source = (ROOT / "app/modules/integrations/product_mapping_service.py").read_text(encoding="utf-8")
    assert 'entity_type = "variant" if variant_id is not None else "product"' in source
    assert "entity_type=entity_type" in source


def test_salla_lookup_uses_product_variant_namespace():
    source = (ROOT / "app/modules/integrations/salla_erp_service.py").read_text(encoding="utf-8")
    assert 'candidates.append((str(item.variant_external_id).strip(), "variant"))' in source
    assert 'candidates.append((str(item.product_external_id).strip(), "product"))' in source
    assert 'IntegrationProductMapping.entity_type == entity_type' in source


def test_namespace_migration_backfills_existing_variant_mappings():
    source = (ROOT / "alembic/versions/20260914_namespace_integration_product_mapping_external_ids.py").read_text(encoding="utf-8")
    assert "UPDATE integration_product_mappings SET entity_type = 'variant' WHERE variant_id IS NOT NULL" in source
    assert '["connection_id", "entity_type", "external_id"]' in source
