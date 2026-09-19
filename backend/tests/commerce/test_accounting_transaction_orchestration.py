from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVICE = (ROOT / "app/modules/commerce/service.py").read_text(encoding="utf-8")
ROUTER = (ROOT / "app/modules/commerce/router.py").read_text(encoding="utf-8")


def test_confirm_orchestrates_invoice_and_note_accounting_in_service():
    assert 'commerce_accounting_service.post_sales_invoice(db, obj, user_id)' in SERVICE
    assert 'commerce_accounting_service.post_sales_credit_note(db, obj, user_id)' in SERVICE
    assert 'commerce_accounting_service.post_purchase_bill(db, obj, user_id)' in SERVICE
    assert 'commerce_accounting_service.post_purchase_debit_note(db, obj, user_id)' in SERVICE


def test_delivery_orchestrates_cogs_after_inventory_in_same_service_call():
    inventory_marker = 'inventory_stock_move_service.post(db, tenant_id=tenant_id, company_id=company_id, move_id=move.id, user_id=user_id)'
    cogs_marker = 'commerce_accounting_service.post_sales_delivery_cogs(db, obj, user_id)'
    assert inventory_marker in SERVICE
    assert cogs_marker in SERVICE
    assert SERVICE.index(inventory_marker) < SERVICE.index(cogs_marker)


def test_payment_and_reversal_accounting_are_orchestrated_once_at_service_boundary():
    assert 'commerce_accounting_service.post_payment(db, payment, document, user_id)' in SERVICE
    assert 'commerce_accounting_service.post_payment_reversal(db, payment, document, user_id, reversal_date=reversal_date)' in SERVICE
    assert ROUTER.count('commerce_accounting_service.post_payment(') == 0
    assert ROUTER.count('commerce_accounting_service.post_payment_reversal(') == 0


def test_router_passes_current_user_to_transaction_orchestrator():
    assert 'commerce_service.confirm(db, company_id, document_id, "sale", current_user.id)' in ROUTER
    assert 'commerce_service.confirm(db, company_id, document_id, "purchase", current_user.id)' in ROUTER
    assert 'commerce_service.post_inventory(db, company_id, document_id, "sale"' in ROUTER
    assert 'commerce_service.post_inventory(db, company_id, document_id, "purchase"' in ROUTER
    assert 'user_id=current_user.id' in ROUTER
    assert 'commerce_service.pay(db, payload, "sale", current_user.id)' in ROUTER
    assert 'commerce_service.pay(db, payload, "purchase", current_user.id)' in ROUTER


def test_document_confirmation_requires_at_least_one_line_before_accounting():
    assert 'if not obj.lines:' in SERVICE
    assert 'raise ValueError("A document must contain at least one line before confirmation")' in SERVICE
