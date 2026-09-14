from decimal import Decimal


def variance(actual: Decimal, budget: Decimal) -> Decimal:
    return actual - budget


def variance_percent(actual: Decimal, budget: Decimal) -> Decimal:
    if budget == 0:
        return Decimal("0") if actual == 0 else Decimal("100")
    return ((actual - budget) / abs(budget)) * Decimal("100")


def contribution_margin(sales: Decimal, variable_cost: Decimal) -> Decimal:
    return sales - variable_cost


def contribution_margin_percent(sales: Decimal, variable_cost: Decimal) -> Decimal:
    if sales == 0:
        return Decimal("0")
    return contribution_margin(sales, variable_cost) / sales * Decimal("100")


def break_even_sales(fixed_cost: Decimal, contribution_margin_pct: Decimal) -> Decimal:
    if contribution_margin_pct <= 0:
        raise ValueError("Contribution margin percentage must be positive")
    return fixed_cost / (contribution_margin_pct / Decimal("100"))


def roi(operating_profit: Decimal, average_operating_assets: Decimal) -> Decimal:
    if average_operating_assets == 0:
        raise ValueError("Average operating assets must not be zero")
    return operating_profit / average_operating_assets * Decimal("100")


def residual_income(operating_profit: Decimal, average_operating_assets: Decimal, required_return_pct: Decimal) -> Decimal:
    required_return = average_operating_assets * required_return_pct / Decimal("100")
    return operating_profit - required_return
