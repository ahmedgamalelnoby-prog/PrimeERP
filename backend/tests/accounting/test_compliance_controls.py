from datetime import date
from decimal import Decimal

import pytest

from app.modules.accounting.compliance_controls import (
    AccountingComplianceError,
    ComplianceContext,
    compliance_snapshot,
    validate_currency,
    validate_double_entry,
    validate_ifrs_transaction,
    validate_period,
    validate_source,
    validate_tax_totals,
)


def test_double_entry_balances():
    assert validate_double_entry([
        {"debit": "100.00", "credit": "0"},
        {"debit": "0", "credit": "100.00"},
    ]) == (Decimal("100.00"), Decimal("100.00"))


def test_double_entry_rejects_unbalanced():
    with pytest.raises(AccountingComplianceError, match="Unbalanced"):
        validate_double_entry([{"debit": "100", "credit": "0"}, {"debit": "0", "credit": "99"}])


def test_double_entry_rejects_nan_and_both_sides():
    with pytest.raises(AccountingComplianceError):
        validate_double_entry([{"debit": "NaN", "credit": "0"}, {"debit": "0", "credit": "NaN"}])
    with pytest.raises(AccountingComplianceError):
        validate_double_entry([{"debit": "10", "credit": "1"}, {"debit": "0", "credit": "9"}])


def test_tax_reconciliation_and_wht_cap():
    validate_tax_totals(taxable_base=Decimal("100"), output_tax=Decimal("14"), withholding=Decimal("5"), gross=Decimal("114"))
    with pytest.raises(AccountingComplianceError):
        validate_tax_totals(taxable_base=Decimal("100"), output_tax=Decimal("14"), withholding=Decimal("115"), gross=Decimal("114"))


def test_period_and_source_controls():
    validate_period(entry_date=date(2026, 9, 14), start_date=date(2026, 9, 1), end_date=date(2026, 9, 30), status="open")
    with pytest.raises(AccountingComplianceError):
        validate_period(entry_date=date(2026, 9, 14), start_date=date(2026, 9, 1), end_date=date(2026, 9, 30), status="closed")
    validate_source(source_module="commerce", source_entity="sales_invoice", source_id=10)
    with pytest.raises(AccountingComplianceError):
        validate_source(source_module="commerce", source_entity="sales_invoice", source_id=None)


def test_currency_requires_positive_rate():
    validate_currency("EGP", Decimal("1"))
    with pytest.raises(AccountingComplianceError):
        validate_currency("EGP", Decimal("0"))


def test_ifrs_15_requires_satisfied_performance_obligation():
    validate_ifrs_transaction(standard="IFRS_15", context={"performance_obligation_satisfied": True, "consideration": Decimal("100")})
    with pytest.raises(AccountingComplianceError, match="performance obligation"):
        validate_ifrs_transaction(standard="IFRS_15", context={"performance_obligation_satisfied": False, "consideration": Decimal("100"), "revenue_recognized": True})
    with pytest.raises(AccountingComplianceError, match="consideration"):
        validate_ifrs_transaction(standard="IFRS_15", context={"performance_obligation_satisfied": True, "consideration": Decimal("-1")})


def test_ias_2_requires_write_down_when_nrv_is_lower():
    with pytest.raises(AccountingComplianceError, match="IAS 2"):
        validate_ifrs_transaction(standard="IAS_2", context={"quantity": 10, "unit_cost": 20, "net_realizable_value": 150})
    validate_ifrs_transaction(standard="IAS_2", context={"quantity": 10, "unit_cost": 20, "net_realizable_value": 150, "impairment_recognized": True})


def test_ifrs_36_impairment_control():
    with pytest.raises(AccountingComplianceError, match="IAS 36"):
        validate_ifrs_transaction(standard="IAS_36", context={"carrying_amount": 1000, "recoverable_amount": 700})


def test_ias_37_provision_control():
    with pytest.raises(AccountingComplianceError, match="provision recognition"):
        validate_ifrs_transaction(standard="IAS_37", context={"present_obligation": True, "probable_outflow": True, "reliably_estimable": True})
    validate_ifrs_transaction(standard="IAS_37", context={"present_obligation": True, "probable_outflow": True, "reliably_estimable": True, "provision_recognized": True})
    with pytest.raises(AccountingComplianceError, match="reliable estimation"):
        validate_ifrs_transaction(standard="IAS_37", context={"present_obligation": True, "probable_outflow": True, "reliably_estimable": False, "provision_recognized": True})


def test_compliance_context_uses_current_date_factory():
    first = ComplianceContext()
    second = ComplianceContext()
    assert first.as_of == date.today()
    assert second.as_of == date.today()


def test_compliance_snapshot_uses_effective_standards():
    snapshot = compliance_snapshot(ComplianceContext(as_of=date(2026, 9, 14)))
    assert snapshot["jurisdiction"] == "EG"
    assert snapshot["accounting_framework"] == "IFRS"
    assert "IFRS_18" not in {standard.code for standard in snapshot["effective_ifrs_standards"]}
    future = compliance_snapshot(ComplianceContext(as_of=date(2027, 1, 1)))
    assert "IFRS_18" in {standard.code for standard in future["effective_ifrs_standards"]}
    assert future["legal_status"] == "configuration_required"
