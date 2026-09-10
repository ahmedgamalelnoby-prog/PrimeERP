from decimal import Decimal

import pytest

from app.modules.accounting.taxes.service import TaxService, TaxValidationError
from app.modules.accounting.withholding_tax.service import WithholdingTaxService, WithholdingTaxValidationError


def test_tax_calculation_rounds_to_currency_precision():
    result = TaxService.calculate(Decimal("1000"), Decimal("14"))
    assert result.tax_amount == Decimal("140.00")
    assert result.total_amount == Decimal("1140.00")


def test_reverse_tax_extracts_tax_from_gross():
    result = TaxService.reverse_tax(Decimal("1140"), Decimal("14"))
    assert result.taxable_amount == Decimal("1000.00")
    assert result.tax_amount == Decimal("140.00")


def test_tax_rejects_invalid_rate():
    with pytest.raises(TaxValidationError):
        TaxService.calculate(100, 101)


def test_withholding_tax_reduces_payable_amount():
    result = WithholdingTaxService.calculate(Decimal("10000"), Decimal("3"))
    assert result.withheld_amount == Decimal("300.00")
    assert result.net_amount == Decimal("9700.00")


def test_withholding_tax_rejects_negative_amount():
    with pytest.raises(WithholdingTaxValidationError):
        WithholdingTaxService.calculate(-1, 3)
