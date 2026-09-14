from decimal import Decimal

from app.modules.catalog.pricing_engine import _money


def test_money_rounding_is_four_decimal_places():
    assert _money(Decimal("12.34567")) == Decimal("12.3457")


def test_margin_recommendation_uses_margin_on_sales_price():
    cost = Decimal("70")
    target_margin = Decimal("30")
    recommended = _money(cost / (Decimal("1") - target_margin / 100))
    assert recommended == Decimal("100.0000")


def test_quantity_tier_ordering_prefers_highest_eligible_minimum_quantity():
    tiers = [Decimal("1"), Decimal("10"), Decimal("50")]
    quantity = Decimal("27")
    eligible = [tier for tier in tiers if tier <= quantity]
    assert max(eligible) == Decimal("10")


def test_quantity_tier_has_no_eligible_price_below_first_tier():
    tiers = [Decimal("10"), Decimal("50")]
    quantity = Decimal("5")
    assert not [tier for tier in tiers if tier <= quantity]
