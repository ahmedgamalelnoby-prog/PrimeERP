from decimal import Decimal

import pytest

from app.modules.uom.service import UOMService


def test_uom_conversion_factor_is_positive():
    with pytest.raises(ValueError):
        UOMService.validate_conversion_factor(Decimal("0"))


def test_uom_conversion():
    assert UOMService.convert(Decimal("2"), Decimal("1"), Decimal("1000")) == Decimal("0.002")
