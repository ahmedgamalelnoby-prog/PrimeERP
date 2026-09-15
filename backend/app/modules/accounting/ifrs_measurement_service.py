"""Deterministic measurement helpers for the principal IFRS transaction classes.

The functions are policy engines, not legal/tax advice. Statutory tax rates and
company-specific elections remain configuration inputs.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

Q = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(Q, rounding=ROUND_HALF_UP)


def ias2_carrying_amount(quantity: Decimal, unit_cost: Decimal, nrv: Decimal) -> dict[str, Decimal]:
    cost = money(quantity * unit_cost)
    nrv_amount = money(nrv)
    carrying = min(cost, nrv_amount)
    return {"cost": cost, "nrv": nrv_amount, "carrying_amount": carrying, "write_down": money(cost - carrying)}


def ias16_straight_line_depreciation(cost: Decimal, residual_value: Decimal, useful_life_months: int, months_in_service: int) -> dict[str, Decimal]:
    if useful_life_months <= 0 or months_in_service < 0:
        raise ValueError("Useful life must be positive and service months cannot be negative")
    depreciable = max(Decimal("0"), cost - residual_value)
    monthly = depreciable / Decimal(useful_life_months)
    accumulated = min(depreciable, monthly * Decimal(months_in_service))
    return {"depreciable_amount": money(depreciable), "monthly_depreciation": money(monthly), "accumulated_depreciation": money(accumulated), "carrying_amount": money(cost - accumulated)}


def ias21_translate(amount: Decimal, exchange_rate: Decimal) -> Decimal:
    if exchange_rate <= 0:
        raise ValueError("Exchange rate must be positive")
    return money(amount * exchange_rate)


def ias36_impairment(carrying_amount: Decimal, recoverable_amount: Decimal) -> dict[str, Decimal]:
    impairment = max(Decimal("0"), carrying_amount - recoverable_amount)
    return {"recoverable_amount": money(recoverable_amount), "impairment_loss": money(impairment), "post_impairment_carrying_amount": money(carrying_amount - impairment)}


def ias37_provision(best_estimate: Decimal, probable_outflow: bool, reliably_estimable: bool) -> Decimal:
    if probable_outflow and reliably_estimable:
        return money(max(Decimal("0"), best_estimate))
    return Decimal("0")


def ifrs9_expected_credit_loss(probability_of_default: Decimal, loss_given_default: Decimal, exposure_at_default: Decimal) -> Decimal:
    for value in (probability_of_default, loss_given_default, exposure_at_default):
        if value < 0:
            raise ValueError("IFRS 9 inputs cannot be negative")
    return money(probability_of_default * loss_given_default * exposure_at_default)


def ifrs15_transaction_price(consideration: Decimal, variable_consideration: Decimal = Decimal("0"), constrained_variable_consideration: Decimal | None = None) -> Decimal:
    variable = variable_consideration if constrained_variable_consideration is None else constrained_variable_consideration
    return money(consideration + variable)


def ifrs15_allocate_transaction_price(transaction_price: Decimal, standalone_prices: list[Decimal]) -> list[Decimal]:
    if not standalone_prices or any(value < 0 for value in standalone_prices) or sum(standalone_prices, Decimal("0")) <= 0:
        raise ValueError("Standalone selling prices must contain positive total consideration")
    total = sum(standalone_prices, Decimal("0"))
    allocations = [money(transaction_price * value / total) for value in standalone_prices]
    allocations[-1] += money(transaction_price - sum(allocations, Decimal("0")))
    return allocations


def ifrs16_initial_measurement(lease_payments_pv: Decimal, initial_direct_costs: Decimal = Decimal("0"), prepayments: Decimal = Decimal("0"), incentives: Decimal = Decimal("0")) -> dict[str, Decimal]:
    if lease_payments_pv < 0 or initial_direct_costs < 0 or prepayments < 0 or incentives < 0:
        raise ValueError("IFRS 16 initial measurement inputs cannot be negative")
    liability = money(lease_payments_pv)
    rou_asset = money(liability + initial_direct_costs + prepayments - incentives)
    return {"lease_liability": liability, "rou_asset": rou_asset}


def ifrs16_monthly_rou_depreciation(rou_asset: Decimal, lease_term_months: int, months_elapsed: int) -> Decimal:
    if lease_term_months <= 0 or months_elapsed < 0:
        raise ValueError("Lease term must be positive and elapsed months cannot be negative")
    return money(min(rou_asset, rou_asset / Decimal(lease_term_months) * Decimal(months_elapsed)))


def ias12_tax_expense(current_tax: Decimal, deferred_tax_expense: Decimal) -> Decimal:
    return money(current_tax + deferred_tax_expense)


def ifrs13_fair_value(*, quoted_price: Decimal | None = None, observable_input_value: Decimal | None = None, valuation_model_value: Decimal | None = None) -> dict[str, object]:
    if quoted_price is not None:
        return {"fair_value": money(quoted_price), "level": 1}
    if observable_input_value is not None:
        return {"fair_value": money(observable_input_value), "level": 2}
    if valuation_model_value is not None:
        return {"fair_value": money(valuation_model_value), "level": 3}
    raise ValueError("At least one IFRS 13 valuation input is required")


def ifrs18_profit_or_loss(operating_income: Decimal, operating_expense: Decimal, investing_income: Decimal = Decimal("0"), investing_expense: Decimal = Decimal("0"), financing_income: Decimal = Decimal("0"), financing_expense: Decimal = Decimal("0"), income_tax: Decimal = Decimal("0")) -> dict[str, Decimal]:
    operating_profit = operating_income - operating_expense
    profit_before_financing_tax = operating_profit + investing_income - investing_expense
    profit_before_tax = profit_before_financing_tax + financing_income - financing_expense
    profit = profit_before_tax - income_tax
    return {"operating_profit": money(operating_profit), "profit_before_financing_and_tax": money(profit_before_financing_tax), "profit_before_tax": money(profit_before_tax), "profit": money(profit)}
