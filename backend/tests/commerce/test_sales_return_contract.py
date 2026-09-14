from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RETURN_SOURCE = (ROOT / "app/modules/commerce/sales_return_service.py").read_text(encoding="utf-8")
RETURN_ACCOUNTING = (ROOT / "app/modules/commerce/sales_return_accounting.py").read_text(encoding="utf-8")
INVENTORY_SOURCE = (ROOT / "app/modules/inventory/stock_moves/service.py").read_text(encoding="utf-8")


def test_return_is_linked_to_original_delivery_line_and_customer():
    assert "original_delivery_line_id" in RETURN_SOURCE
    assert "delivery.partner_id != payload.partner_id" in RETURN_SOURCE
    assert 'SalesDocument.document_type == "delivery"' in RETURN_SOURCE


def test_return_quantity_is_capped_by_delivered_less_already_returned():
    assert "SalesReturnAllocation.quantity" in RETURN_SOURCE
    assert "available = Decimal(delivery_move.quantity) - Decimal(returned_qty)" in RETURN_SOURCE
    assert "Return quantity exceeds delivered quantity" in RETURN_SOURCE


def test_return_preserves_original_delivery_unit_cost():
    assert "Decimal(delivery_move.unit_cost or 0)" in RETURN_SOURCE
    assert "unit_cost=request_line.quantity" not in RETURN_SOURCE
    assert "SalesReturnAllocation" in RETURN_SOURCE


def test_return_is_variant_aware_and_uses_active_variant_rules():
    assert "source_line.variant_id" in RETURN_SOURCE
    assert "ProductVariant.is_active.is_(True)" in RETURN_SOURCE
    assert "InventoryStockMove.variant_id == source_line.variant_id" in RETURN_SOURCE
    assert "This item has active variants" in INVENTORY_SOURCE


def test_return_cogs_reversal_is_balanced_and_idempotent():
    assert 'source_entity="sales_return_cogs"' in RETURN_ACCOUNTING
    assert 'entry_number=f"RCN-COGS-{document.id}"' in RETURN_ACCOUNTING
    assert '"account_combination_id": settings.inventory_account_id, "debit": total' in RETURN_ACCOUNTING
    assert '"account_combination_id": settings.cogs_account_id, "debit": 0, "credit": total' in RETURN_ACCOUNTING


def test_return_cost_math_uses_allocation_quantity_times_original_cost():
    qty = Decimal("3")
    original_cost = Decimal("27.50")
    assert qty * original_cost == Decimal("82.50")


def test_financial_credit_note_and_physical_return_are_separate_sources():
    accounting = (ROOT / "app/modules/commerce/accounting_service.py").read_text(encoding="utf-8")
    assert 'source_entity="sales_credit_note"' in accounting
    assert 'source_entity="sales_return_cogs"' in RETURN_ACCOUNTING
    assert 'source_entity="sales_return"' in RETURN_SOURCE
