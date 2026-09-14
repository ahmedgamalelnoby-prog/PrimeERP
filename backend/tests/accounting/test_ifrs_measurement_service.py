from decimal import Decimal

import pytest

from app.modules.accounting.ifrs_measurement_service import (
    ias2_carrying_amount,
    ias16_straight_line_depreciation,
    ias21_translate,
    ias36_impairment,
    ias37_provision,
    ias12_tax_expense,
    ifrs9_expected_credit_loss,
    ifrs13_fair_value,
    ifrs15_allocate_transaction_price,
    ifrs15_transaction_price,
    ifrs16_initial_measurement,
    ifrs16_monthly_rou_depreciation,
    ifrs18_profit_or_loss,
)


def test_ias2_lower_of_cost_and_nrv():
    result = ias2_carrying_amount(quantity=Decimal("10"), unit_cost=Decimal("20"), nrv=Decimal("150"))
    assert result["carrying_amount"] == Decimal("150.00")
    assert result["write_down"] == Decimal("50.00")


def test_ias16_depreciation():
    result = ias16_straight_line_depreciation(cost=Decimal("1200"), residual_value=Decimal("0"), useful_life_months=12, months_in_service=3)
    assert result["monthly_depreciation"] == Decimal("100.00")
    assert result["carrying_amount"] == Decimal("900.00")


def test_ias21_and_ias36():
    assert ias21_translate(Decimal("100"), Decimal("50")) == Decimal("5000.00")
    result = ias36_impairment(carrying_amount=Decimal("1000"), recoverable_amount=Decimal("700"))
    assert result["impairment_loss"] == Decimal("300.00")


def test_ias37_provision_requires_probability_and_reliable_estimate():
    assert ias37_provision(best_estimate=Decimal("100"), probable_outflow=True, reliably_estimable=True) == Decimal("100.00")
    assert ias37_provision(best_estimate=Decimal("100"), probable_outflow=False, reliably_estimable=True) == Decimal("0")


def test_ifrs9_ecl():
    assert ifrs9_expected_credit_loss(Decimal("0.10"), Decimal("0.40"), Decimal("1000")) == Decimal("40.00")


def test_ifrs15_allocation():
    assert ifrs15_transaction_price(Decimal("1000"), Decimal("100")) == Decimal("1100.00")
    assert ifrs15_allocate_transaction_price(Decimal("900"), [Decimal("600"), Decimal("300")]) == [Decimal("600.00"), Decimal("300.00")]


def test_ifrs16_measurement():
    initial = ifrs16_initial_measurement(lease_payments_pv=Decimal("1200"), initial_direct_costs=Decimal("100"))
    assert initial == {"lease_liability": Decimal("1200.00"), "rou_asset": Decimal("1300.00")}
    assert ifrs16_monthly_rou_depreciation(Decimal("1200"), 12, 3) == Decimal("300.00")


def test_ias12_ifrs13_ifrs18():
    assert ias12_tax_expense(Decimal("100"), Decimal("20")) == Decimal("120.00")
    assert ifrs13_fair_value(quoted_price=Decimal("55"))["level"] == 1
    result = ifrs18_profit_or_loss(Decimal("1000"), Decimal("600"), financing_expense=Decimal("50"), income_tax=Decimal("70"))
    assert result["operating_profit"] == Decimal("400.00")
    assert result["profit"] == Decimal("280.00")


def test_invalid_ifrs_measurement_inputs():
    with pytest.raises(ValueError):
        ias16_straight_line_depreciation(cost=Decimal("100"), residual_value=Decimal("0"), useful_life_months=0, months_in_service=1)
    with pytest.raises(ValueError):
        ifrs13_fair_value()
