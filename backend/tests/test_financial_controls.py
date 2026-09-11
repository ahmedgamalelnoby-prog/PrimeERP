from decimal import Decimal

from app.modules.accounting.withholding_tax.service import withholding_tax_service


def test_withholding_tax_calculation_is_balanced():
    result = withholding_tax_service.calculate(Decimal("10000"), Decimal("3"))
    assert result.gross_amount == Decimal("10000")
    assert result.withheld_amount == Decimal("300.00")
    assert result.net_amount == Decimal("9700.00")
    assert result.withheld_amount + result.net_amount == result.gross_amount


def test_zero_withholding_preserves_gross():
    result = withholding_tax_service.calculate("1250.50", "0")
    assert result.withheld_amount == Decimal("0.00")
    assert result.net_amount == Decimal("1250.50")


def test_invalid_withholding_rate_is_rejected():
    try:
        withholding_tax_service.calculate("100", "100.01")
    except ValueError:
        pass
    else:
        raise AssertionError("A withholding rate above 100% must be rejected")
