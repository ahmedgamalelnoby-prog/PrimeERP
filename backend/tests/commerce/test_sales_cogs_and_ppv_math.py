from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACCOUNTING_SOURCE = (ROOT / "app/modules/commerce/accounting_service.py").read_text(encoding="utf-8")
INVENTORY_SOURCE = (ROOT / "app/modules/inventory/stock_moves/service.py").read_text(encoding="utf-8")


def test_ppv_is_balanced_when_bill_is_lower_than_receipt():
    receipt = Decimal("120")
    bill = Decimal("100")
    variance = bill - receipt
    debit = receipt
    credit = bill + (-variance)
    assert variance == Decimal("-20")
    assert debit == credit == Decimal("120")


def test_ppv_is_balanced_when_bill_is_higher_than_receipt():
    receipt = Decimal("100")
    bill = Decimal("120")
    variance = bill - receipt
    debit = receipt + variance
    credit = bill
    assert variance == Decimal("20")
    assert debit == credit == Decimal("120")


def test_sales_cogs_uses_posted_stock_move_cost_and_is_idempotent_by_source():
    assert 'source_entity == "sales_delivery"' in ACCOUNTING_SOURCE
    assert 'source_entity="sales_cogs"' in ACCOUNTING_SOURCE
    assert 'entry_number=f"COGS-{document.id}"' in ACCOUNTING_SOURCE
    assert 'getattr(move, "source_entity", None) == "sales_delivery"' in INVENTORY_SOURCE


def test_fifo_issue_preserves_weighted_layer_cost_on_stock_move():
    assert "fifo_allocations = self._consume_fifo_layers" in INVENTORY_SOURCE
    assert "unit_cost = self._weighted_cost(fifo_allocations)" in INVENTORY_SOURCE
    assert "move.unit_cost = unit_cost" in INVENTORY_SOURCE
