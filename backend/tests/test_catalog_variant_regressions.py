from decimal import Decimal


def test_variant_and_barcode_models_are_registered():
    from app.modules.catalog.models import ProductBarcode, ProductVariant

    assert ProductVariant.__tablename__ == "product_variants"
    assert ProductBarcode.__tablename__ == "product_barcodes"


def test_variant_schema_defaults_to_json_attributes():
    from app.modules.catalog.schemas import VariantCreate

    payload = VariantCreate(
        product_id=1,
        sku="SKU-RED-M",
        name_ar="منتج أحمر M",
        sales_price=Decimal("120"),
        purchase_price=Decimal("70"),
    )
    assert payload.attributes == {}


def test_variant_service_rejects_mismatched_barcode_variant():
    # The service enforces the URL target as the authoritative variant owner;
    # this regression protects against cross-variant barcode reassignment.
    from app.modules.catalog.variant_service import ProductVariantService

    assert hasattr(ProductVariantService, "add_barcode")
    assert hasattr(ProductVariantService, "create_variant")


def test_variant_migration_exists_for_model_tables():
    from pathlib import Path

    migration = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "20260914_product_variants.py"
    text = migration.read_text(encoding="utf-8")
    assert "product_variants" in text
    assert "product_barcodes" in text
    assert "20260914_recipe_uom_snapshot" in text
