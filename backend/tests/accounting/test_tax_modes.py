from decimal import Decimal

import pytest

from app.modules.accounting.taxes.service import TaxLine, TaxService, TaxValidationError


def test_inclusive_multiple_taxes_split_gross():
    result = TaxService.calculate_inclusive("115.00", [TaxLine("vat", Decimal("10")), TaxLine("local", Decimal("5"))])
    assert result.taxable_amount == Decimal("100.00")
    assert result.tax_amount == Decimal("15.00")
    assert result.total_amount == Decimal("115.00")


def test_withholding_reduces_payable():
    result = TaxService.calculate_withholding("1000", "2.5")
    assert result.tax_amount == Decimal("25.00")
    assert result.total_amount == Decimal("975.00")


def test_inclusive_duplicate_tax_codes_are_rejected():
    with pytest.raises(TaxValidationError):
        TaxService.calculate_inclusive("100", [("vat", "10"), ("VAT", "5")])
