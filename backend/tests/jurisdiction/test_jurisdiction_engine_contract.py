from datetime import date
from decimal import Decimal

import pytest

from app.modules.jurisdiction.service import JurisdictionContext, JurisdictionEngine


def test_context_requires_place_of_supply_and_item_type():
    with pytest.raises(ValueError, match="Place of supply"):
        JurisdictionEngine._validate_context(
            JurisdictionContext(
                company_id=1,
                partner_id=2,
                transaction_type="sale",
                transaction_date=date(2026, 1, 1),
                place_of_supply=None,
                goods_or_services="goods",
            )
        )

    with pytest.raises(ValueError, match="goods_or_services"):
        JurisdictionEngine._validate_context(
            JurisdictionContext(
                company_id=1,
                partner_id=2,
                transaction_type="sale",
                transaction_date=date(2026, 1, 1),
                place_of_supply="local",
                goods_or_services=None,
            )
        )


def test_condition_matching_supports_full_transaction_facts():
    ctx = JurisdictionContext(
        company_id=1,
        partner_id=2,
        transaction_type="sale",
        transaction_date=date(2026, 1, 1),
        place_of_supply="destination",
        b2b=False,
        goods_or_services="services",
        import_export="export",
        facts={"special_scheme": "standard"},
    )

    class Rule:
        conditions = {
            "b2b": False,
            "goods_or_services": "services",
            "import_export": "export",
            "special_scheme": {"eq": "standard"},
        }

    assert JurisdictionEngine._condition_matches(Rule(), ctx) is True


def test_tax_calculation_rejects_negative_inputs():
    with pytest.raises(ValueError):
        JurisdictionEngine.calculate_tax(Decimal("-1"), Decimal("15"))
    with pytest.raises(ValueError):
        JurisdictionEngine.calculate_tax(Decimal("100"), Decimal("-1"))
