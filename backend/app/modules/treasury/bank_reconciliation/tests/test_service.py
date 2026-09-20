import pytest
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.modules.treasury.bank_reconciliation.service import fingerprint_line, create_statement


def test_statement_fingerprint_is_stable():
    p=SimpleNamespace(external_id="x1",transaction_date=date(2026,9,19),value_date=None,reference="R",cheque_number=None,debit=Decimal("10"),credit=Decimal("0"),currency="EGP",description="test")
    assert fingerprint_line(p)==fingerprint_line(p)


def test_statement_fingerprint_changes_with_amount():
    p=SimpleNamespace(external_id="x1",transaction_date=date(2026,9,19),value_date=None,reference="R",cheque_number=None,debit=Decimal("10"),credit=Decimal("0"),currency="EGP",description="test")
    q=SimpleNamespace(**{**p.__dict__,"debit":Decimal("11")})
    assert fingerprint_line(p)!=fingerprint_line(q)


class ScalarStub:
    def __init__(self, values):
        self.values=iter(values)
    def scalar(self, query):
        return next(self.values)


def test_create_statement_rejects_overlapping_period():
    account=SimpleNamespace(id=1,company_id=10,opening_balance=Decimal("0"))
    existing=SimpleNamespace(id=7)
    db=ScalarStub([account, existing])
    user=SimpleNamespace(tenant_id=1)
    payload=SimpleNamespace(company_id=10,bank_account_id=1,period_start=date(2026,9,1),period_end=date(2026,9,30),opening_balance=Decimal("0"),closing_balance=Decimal("0"))
    with pytest.raises(ValueError, match="overlaps"):
        create_statement(db,payload,user)


def test_reconciliation_source_filters_exclude_closed_cheques():
    source = __import__("inspect").getsource(__import__("app.modules.treasury.bank_reconciliation.service", fromlist=["match"]).match)
    assert 'Cheque.status.in_(["received","deposited","under_collection","resubmitted","issued","collected","cleared"])' in source


def test_reconciliation_import_rejects_same_external_id_with_changed_details():
    source = __import__("inspect").getsource(__import__("app.modules.treasury.bank_reconciliation.service", fromlist=["add_line"]).add_line)
    assert "Statement external_id already exists with different transaction details" in source


def test_reconciliation_line_is_locked_before_matching():
    source = __import__("inspect").getsource(__import__("app.modules.treasury.bank_reconciliation.service", fromlist=["_line"])._line)
    assert ".with_for_update()" in source


def test_reconciliation_source_uniqueness_matches_database_constraint():
    source = __import__("inspect").getsource(__import__("app.modules.treasury.bank_reconciliation.models", fromlist=["ReconciliationMatch"]).ReconciliationMatch)
    assert 'UniqueConstraint("session_id", "source_type", "source_id", name="uq_treasury_reconciliation_match_session_source")' in source


def test_close_session_locks_company_scoped_statement():
    source = __import__("inspect").getsource(__import__("app.modules.treasury.bank_reconciliation.service", fromlist=["close_session"]).close_session)
    assert "BankStatement.company_id==session.company_id" in source
    assert "BankStatement.bank_account_id==session.bank_account_id" in source
    assert ".with_for_update()" in source


def test_unmatch_locks_company_scoped_statement_line():
    source = __import__("inspect").getsource(__import__("app.modules.treasury.bank_reconciliation.service", fromlist=["unmatch"]).unmatch)
    assert "BankStatementLine.company_id==session.company_id" in source
    assert "BankStatementLine.statement_id==session.statement_id" in source
    assert ".with_for_update()" in source
