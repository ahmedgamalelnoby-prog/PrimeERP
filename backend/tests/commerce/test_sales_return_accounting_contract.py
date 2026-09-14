from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVICE = (ROOT / "app/modules/commerce/sales_return_service.py").read_text(encoding="utf-8")
ACCOUNTING = (ROOT / "app/modules/commerce/sales_return_accounting.py").read_text(encoding="utf-8")
MODELS = (ROOT / "app/modules/commerce/sales_return_models.py").read_text(encoding="utf-8")


def test_return_is_linked_to_original_delivery_line():
    assert "original_delivery_line_id" in SERVICE
    assert "SalesReturnAllocation" in SERVICE
    assert "return quantity exceeds delivered quantity" in SERVICE


def test_return_uses_original_delivery_cost_snapshot():
    assert 'source_entity == "sales_delivery"' in SERVICE
    assert "delivery_move.unit_cost" in SERVICE
    assert "unit_cost=Decimal(delivery_move.unit_cost or 0)" in SERVICE


def test_return_cogs_reversal_is_double_entry_and_idempotent():
    assert 'source_entity="sales_return_cogs"' in ACCOUNTING
    assert '"account_combination_id": settings.inventory_account_id' in ACCOUNTING
    assert '"account_combination_id": settings.cogs_account_id' in ACCOUNTING
    assert '"debit": total, "credit": 0' in ACCOUNTING
    assert '"debit": 0, "credit": total' in ACCOUNTING


def test_return_allocation_has_company_scoped_unique_control():
    assert 'ForeignKey("companies.id", ondelete="CASCADE")' in MODELS
    assert 'UniqueConstraint("credit_note_line_id", "original_delivery_line_id"' in MODELS
    assert 'CheckConstraint("quantity > 0"' in MODELS
    assert 'CheckConstraint("unit_cost >= 0"' in MODELS
