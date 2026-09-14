from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sales_line_has_nullable_variant_foreign_key():
    source = (ROOT / "app/modules/commerce/models.py").read_text(encoding="utf-8")
    assert "variant_id = Column(Integer, ForeignKey(\"product_variants.id\", ondelete=\"RESTRICT\"), nullable=True, index=True)" in source


def test_document_line_schema_exposes_variant_id():
    source = (ROOT / "app/modules/commerce/schemas.py").read_text(encoding="utf-8")
    assert "variant_id: int | None = Field(default=None, gt=0)" in source


def test_commerce_validates_variant_company_and_parent_product():
    source = (ROOT / "app/modules/commerce/service.py").read_text(encoding="utf-8")
    assert "ProductVariant.company_id == company_id" in source
    assert "ProductVariant.product_id == item.id" in source
    assert "ProductVariant.is_active.is_(True)" in source
    assert "self._resolve_line_variant" in source


def test_sales_line_variant_migration_is_after_mapping_heads():
    source = (ROOT / "alembic/versions/20260914_sales_line_variant.py").read_text(encoding="utf-8")
    assert 'down_revision = "20260914_fix_integration_product_mapping_local_unique"' in source
    assert 'op.add_column("sales_lines"' in source
    assert '"fk_sales_lines_variant_id"' in source
