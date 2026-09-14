from datetime import date
from decimal import Decimal
from pathlib import Path

from app.modules.jurisdiction.service import JurisdictionEngine


ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "app/modules/jurisdiction/service.py"
MODELS = ROOT / "app/modules/jurisdiction/models.py"


def test_tax_math_is_deterministic_and_non_negative():
    assert JurisdictionEngine.calculate_tax(Decimal("1000"), Decimal("14")) == Decimal("140.0000")
    assert JurisdictionEngine.calculate_tax(Decimal("99.99"), Decimal("15")) == Decimal("14.9985")


def test_tax_math_rejects_negative_values():
    try:
        JurisdictionEngine.calculate_tax(Decimal("-1"), Decimal("15"))
    except ValueError:
        pass
    else:
        raise AssertionError("negative tax base must be rejected")


def test_models_are_effective_dated_and_country_agnostic():
    text = MODELS.read_text(encoding="utf-8")
    assert "effective_from" in text
    assert "effective_to" in text
    assert "country_code" in text
    assert "jurisdiction_id" in text
    assert "EG" not in text


def test_engine_uses_transaction_facts_not_partner_country_alone():
    text = SERVICE.read_text(encoding="utf-8")
    assert "company_id" in text
    assert "partner_id" in text
    assert "transaction_type" in text
    assert "transaction_date" in text
    assert "place_of_supply" in text
    assert "b2b" in text
    assert "import_export" in text
    assert "tax_resident" in text
    assert "vat_registered" in text


def test_transaction_date_is_used_for_rule_selection():
    text = SERVICE.read_text(encoding="utf-8")
    assert "effective_from <= effective_date" in text
    assert "effective_to.is_(None)" in text
    assert "ctx.transaction_date" in text
