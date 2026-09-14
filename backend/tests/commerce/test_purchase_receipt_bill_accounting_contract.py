from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ACCOUNTING_SOURCE = (ROOT / "app/modules/commerce/accounting_service.py").read_text(encoding="utf-8")
SERVICE_SOURCE = (ROOT / "app/modules/commerce/service.py").read_text(encoding="utf-8")
ROUTER_SOURCE = (ROOT / "app/modules/commerce/router.py").read_text(encoding="utf-8")


def test_purchase_receipt_uses_grni_not_ap_or_direct_bill_inventory_double_post():
    assert "def post_purchase_receipt(" in ACCOUNTING_SOURCE
    assert 'source_entity="purchase_receipt_accounting"' in ACCOUNTING_SOURCE
    assert "settings.grni_account_id" in ACCOUNTING_SOURCE
    assert 'source_entity="purchase_bill"' in ACCOUNTING_SOURCE
    assert 'account = settings.grni_account_id if has_receipt else settings.inventory_account_id' in ACCOUNTING_SOURCE


def test_purchase_receipt_accounting_is_inside_service_transaction():
    assert 'if kind == "purchase":' in SERVICE_SOURCE
    assert "commerce_accounting_service.post_purchase_receipt(db, obj" in SERVICE_SOURCE
    assert 'user_id=current_user.id' in ROUTER_SOURCE
    assert 'commerce_service.post_inventory(db, company_id, document_id, "purchase", user_id=current_user.id)' in ROUTER_SOURCE


def test_grni_is_required_in_new_accounting_configuration():
    schema = (ROOT / "app/modules/commerce/accounting_schemas.py").read_text(encoding="utf-8")
    router = ROUTER_SOURCE
    assert "grni_account_id: int = Field(gt=0)" in schema
    assert '"GRNI account": payload.grni_account_id' in router
