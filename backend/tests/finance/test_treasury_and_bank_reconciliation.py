from decimal import Decimal
from app.modules.treasury.schemas import PaymentCreate, PaymentMethodCreate
from app.modules.accounting.bank_reconciliation.schemas import StatementLineCreate

def test_payment_contract():
    payload = PaymentCreate.model_validate({"company_id":1,"payment_method_id":2,"party_type":"customer","party_id":3,"direction":"receipt","payment_date":"2026-09-11","amount":"1250.50"})
    assert payload.amount == Decimal("1250.50")

def test_payment_method_requires_identity():
    payload = PaymentMethodCreate.model_validate({"company_id":1,"code":"CASH","name":"Cash","method_type":"cash"})
    assert payload.is_incoming is True

def test_statement_contract():
    payload = StatementLineCreate.model_validate({"company_id":1,"bank_account_id":2,"statement_date":"2026-09-11","amount":"1250.50","direction":"credit"})
    assert payload.amount == Decimal("1250.50")
