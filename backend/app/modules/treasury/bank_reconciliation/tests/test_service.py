from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from app.modules.treasury.bank_reconciliation.service import fingerprint_line

def test_statement_fingerprint_is_stable():
    p=SimpleNamespace(external_id="x1",transaction_date=date(2026,9,19),value_date=None,reference="R",cheque_number=None,debit=Decimal("10"),credit=Decimal("0"),currency="EGP",description="test")
    assert fingerprint_line(p)==fingerprint_line(p)

def test_statement_fingerprint_changes_with_amount():
    p=SimpleNamespace(external_id="x1",transaction_date=date(2026,9,19),value_date=None,reference="R",cheque_number=None,debit=Decimal("10"),credit=Decimal("0"),currency="EGP",description="test")
    q=SimpleNamespace(**{**p.__dict__,"debit":Decimal("11")})
    assert fingerprint_line(p)!=fingerprint_line(q)
