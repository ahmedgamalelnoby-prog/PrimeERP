from decimal import Decimal

import pytest

from app.modules.accounting.taxes.service import TaxLine, TaxService, TaxValidationError


def test_multiple_taxes_are_calculated_on_the_same_base():
    result = TaxService.calculate_multi(
        Decimal("1000"),
        [TaxLine("vat", Decimal("14")), TaxLine("stamp", Decimal("1.5"))],
    )
    assert result.taxable_amount == Decimal("1000")
    assert [line.tax_amount for line in result.tax_lines] == [Decimal("140.00"), Decimal("15.00")]
    assert result.tax_amount == Decimal("155.00")
    assert result.total_amount == Decimal("1155.00")


def test_multiple_taxes_reject_duplicate_codes():
    with pytest.raises(TaxValidationError, match="Duplicate tax code"):
        TaxService.calculate_multi(1000, [("vat", 14), ("VAT", 5)])


def test_multiple_taxes_allow_no_tax_components():
    result = TaxService.calculate_multi(Decimal("1000"), [])
    assert result.tax_amount == Decimal("0.00")
    assert result.total_amount == Decimal("1000")
