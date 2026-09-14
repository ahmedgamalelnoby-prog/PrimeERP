from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.modules.taxes.schemas import TaxRateBase
from app.modules.taxes.service import normalize_tax_master


def test_tax_master_normalizes_code_and_type() -> None:
    values = normalize_tax_master(
        code=" vat14 ",
        name=" VAT 14% ",
        rate="14",
        tax_type="VAT",
        is_withholding=False,
    )
    assert values == {
        "code": "VAT14",
        "name": "VAT 14%",
        "rate": Decimal("14"),
        "tax_type": "vat",
        "is_withholding": False,
    }


def test_wht_requires_withholding_flag() -> None:
    with pytest.raises(HTTPException) as exc:
        normalize_tax_master(code="WHT5", name="WHT 5%", rate=5, tax_type="wht")
    assert exc.value.status_code == 422


def test_withholding_requires_wht_type() -> None:
    with pytest.raises(HTTPException) as exc:
        normalize_tax_master(code="VAT14", name="VAT 14%", rate=14, tax_type="vat", is_withholding=True)
    assert exc.value.status_code == 422


def test_tax_rate_schema_rejects_invalid_rate() -> None:
    with pytest.raises(ValueError):
        TaxRateBase(code="VAT", name="VAT", rate=Decimal("101"), tax_type="vat")


def test_tax_rate_schema_rejects_invalid_tax_type() -> None:
    with pytest.raises(ValueError):
        TaxRateBase(code="X", name="X", rate=Decimal("5"), tax_type="income")
