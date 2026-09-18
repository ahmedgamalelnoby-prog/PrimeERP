from datetime import date
from decimal import Decimal

from app.modules.shipping.models import ShippingCarrier
from app.modules.shipping.pricing_models import ShippingPricingProfile, ShippingPricingRule
from app.modules.shipping.pricing_schemas import ShippingCostInput
from app.modules.shipping.pricing_service import ShippingPricingService


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def all(self):
        return self.value


class FakeDB:
    def __init__(self, carrier, profile, rules):
        self.carrier = carrier
        self.profile = profile
        self.rules = rules

    def scalar(self, stmt):
        text = str(stmt)
        if "shipping_carriers" in text:
            return self.carrier
        return self.profile

    def scalars(self, stmt):
        return _ScalarResult(self.rules)


def make_carrier():
    return ShippingCarrier(id=1, company_id=1, code="C1", name="Carrier 1", is_active=True)


def make_profile():
    return ShippingPricingProfile(
        id=10, company_id=1, carrier_id=1, name="Standard", effective_from=date(2026, 1, 1),
        effective_to=None, priority=100, is_active=True,
    )


def test_fixed_plus_cod_and_card_fees():
    rules = [
        ShippingPricingRule(id=1, profile_id=10, rule_type="base", basis="order", fixed_amount=50),
        ShippingPricingRule(id=2, profile_id=10, rule_type="cod", basis="cod", percent_rate=1.5),
        ShippingPricingRule(id=3, profile_id=10, rule_type="card", basis="cod", percent_rate=2),
    ]
    payload = ShippingCostInput(
        company_id=1, carrier_id=1, calculation_date=date(2026, 9, 18),
        cod_amount=1000, cod_collected=1000, card_amount=1000,
    )
    result = ShippingPricingService().calculate(FakeDB(make_carrier(), make_profile(), rules), payload)
    assert result.base_shipping == Decimal("50.00")
    assert result.cod_fee == Decimal("15.00")
    assert result.card_fee == Decimal("20.00")
    assert result.total_cost == Decimal("85.00")


def test_weight_rule_with_included_units_and_minimum_floor():
    rules = [
        ShippingPricingRule(id=1, profile_id=10, rule_type="weight", basis="weight", min_value=0, max_value=100, included_units=5, fixed_amount=50, unit_amount=10),
        ShippingPricingRule(id=2, profile_id=10, rule_type="minimum", basis="order", minimum_amount=40),
    ]
    payload = ShippingCostInput(
        company_id=1, carrier_id=1, calculation_date=date(2026, 9, 18),
        weight_kg=8,
    )
    result = ShippingPricingService().calculate(FakeDB(make_carrier(), make_profile(), rules), payload)
    assert result.other_fees == Decimal("80.00")
    assert result.total_cost == Decimal("80.00")


def test_zone_and_remote_surcharge():
    rules = [
        ShippingPricingRule(id=1, profile_id=10, rule_type="zone", basis="order", zone_code="ALEX", fixed_amount=55),
        ShippingPricingRule(id=2, profile_id=10, rule_type="remote", basis="order", fixed_amount=30),
    ]
    payload = ShippingCostInput(
        company_id=1, carrier_id=1, calculation_date=date(2026, 9, 18),
        zone_code="ALEX", remote_area=True,
    )
    result = ShippingPricingService().calculate(FakeDB(make_carrier(), make_profile(), rules), payload)
    assert result.other_fees == Decimal("55.00")
    assert result.surcharge_remote == Decimal("30.00")
    assert result.total_cost == Decimal("85.00")
