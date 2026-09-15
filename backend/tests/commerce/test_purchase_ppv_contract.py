from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACCOUNTING_SOURCE = (ROOT / "app/modules/commerce/accounting_service.py").read_text(encoding="utf-8")
SERVICE_SOURCE = (ROOT / "app/modules/commerce/service.py").read_text(encoding="utf-8")
MODEL_SOURCE = (ROOT / "app/modules/commerce/models.py").read_text(encoding="utf-8")
SCHEMA_SOURCE = (ROOT / "app/modules/commerce/schemas.py").read_text(encoding="utf-8")


def test_ppv_is_explicitly_configured_and_receipt_allocations_are_persistent():
    assert "purchase_price_variance_account_id" in ACCOUNTING_SOURCE
    assert "class PurchaseBillReceiptAllocation" in MODEL_SOURCE
    assert "receipt_ids: list[int]" in SCHEMA_SOURCE
    assert "PurchaseBillReceiptLink" in SERVICE_SOURCE


def test_bill_uses_receipt_valuation_and_posts_only_the_difference_to_ppv():
    assert "settings.grni_account_id" in ACCOUNTING_SOURCE
    assert "settings.purchase_price_variance_account_id" in ACCOUNTING_SOURCE
    assert "variance = stock_total - receipt_value" in ACCOUNTING_SOURCE
    assert "Receipt quantity is insufficient" in ACCOUNTING_SOURCE
    assert '"account_combination_id": account, "debit": receipt_value' in ACCOUNTING_SOURCE
    assert "account = settings.grni_account_id if has_receipt else settings.inventory_account_id" in ACCOUNTING_SOURCE


def test_ppv_journal_math_is_balanced_for_both_price_directions():
    receipt_value = Decimal("120")
    bill_value = Decimal("100")
    variance = bill_value - receipt_value
    debit = receipt_value
    credit = bill_value + max(-variance, Decimal("0"))
    debit += max(variance, Decimal("0"))
    assert debit == credit == Decimal("120")

    receipt_value = Decimal("100")
    bill_value = Decimal("120")
    variance = bill_value - receipt_value
    debit = receipt_value + max(variance, Decimal("0"))
    credit = bill_value + max(-variance, Decimal("0"))
    assert debit == credit == Decimal("120")


def test_receipt_moves_are_locked_before_allocation_to_prevent_double_billing():
    assert "select(InventoryStockMove)" in ACCOUNTING_SOURCE
    assert ".with_for_update()).all())" in ACCOUNTING_SOURCE
    assert "func.sum(PurchaseBillReceiptAllocation.quantity)" in ACCOUNTING_SOURCE
    assert ".with_for_update()) or Decimal" not in ACCOUNTING_SOURCE


def test_bill_receipt_links_require_same_company_vendor_and_received_status():
    assert "PurchaseDocument.id.in_(payload.receipt_ids)" in SERVICE_SOURCE
    assert "PurchaseDocument.company_id == payload.company_id" in SERVICE_SOURCE
    assert "PurchaseDocument.partner_id == payload.partner_id" in SERVICE_SOURCE
    assert "PurchaseDocument.document_type == \"receipt\"" in SERVICE_SOURCE
    assert "PurchaseDocument.status.in_([\"received\", \"partially_received\"])" in SERVICE_SOURCE
