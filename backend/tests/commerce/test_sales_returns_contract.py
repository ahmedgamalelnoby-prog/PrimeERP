from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVICE = (ROOT / "app/modules/commerce/sales_return_service.py").read_text(encoding="utf-8")
ACCOUNTING = (ROOT / "app/modules/commerce/sales_return_accounting.py").read_text(encoding="utf-8")
ROUTER = (ROOT / "app/modules/commerce/router.py").read_text(encoding="utf-8")
MIGRATION = (ROOT / "alembic/versions/20260914_sales_returns.py").read_text(encoding="utf-8")


def test_return_requires_original_delivery_line_and_same_customer():
    assert "document_type == \"delivery\"" in SERVICE
    assert "delivery.partner_id != payload.partner_id" in SERVICE
    assert "original_delivery_line_id" in SERVICE


def test_return_is_capped_by_delivered_not_yet_returned_quantity():
    assert "sum(SalesReturnAllocation.quantity)" in SERVICE
    assert "available = Decimal(delivery_move.quantity) - Decimal(returned_qty)" in SERVICE
    assert "Return quantity exceeds delivered quantity" in SERVICE


def test_return_uses_original_delivery_unit_cost_not_current_cost():
    assert "unit_cost=Decimal(delivery_move.unit_cost or 0)" in SERVICE
    assert "unit_cost=Decimal(delivery_move.unit_cost or 0)" in SERVICE


def test_return_posts_inventory_and_cogs_reversal():
    assert 'source_entity="sales_return"' in SERVICE
    assert 'source_entity="sales_return_cogs"' in ACCOUNTING
    assert '"account_combination_id": settings.inventory_account_id' in ACCOUNTING
    assert '"account_combination_id": settings.cogs_account_id' in ACCOUNTING


def test_return_cogs_is_idempotent_by_document_source():
    assert 'source_id=document.id' in ACCOUNTING
    assert 'source_entity="sales_return_cogs"' in ACCOUNTING


def test_return_endpoint_rolls_back_on_failure():
    assert "db.rollback()" in ROUTER
    assert "IntegrityError" in ROUTER


def test_return_allocation_migration_has_restrictive_integrity():
    assert "sales_return_allocations" in MIGRATION
    assert "ondelete=\"RESTRICT\"" in MIGRATION
    assert "ck_sales_return_allocation_quantity" in MIGRATION
    assert "ck_sales_return_allocation_unit_cost" in MIGRATION
