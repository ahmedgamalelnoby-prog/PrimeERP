from app.core.module_engine.identity import (
    business_code_for_technical,
    canonical_business_code,
    technical_modules_for,
)


def test_einvoice_aliases_share_one_business_identity():
    assert canonical_business_code("egyptian_einvoice") == "einvoice"
    assert canonical_business_code("einvoice") == "einvoice"
    assert business_code_for_technical("localization/egypt_einvoice") == "einvoice"


def test_accounting_has_one_business_identity_for_all_technical_parts():
    modules = technical_modules_for("accounting")
    assert "accounting/accounting_core" in modules
    assert "accounting/journal_entries" in modules
    assert "accounting/vat" in modules
    assert canonical_business_code("accounting") == "accounting"


def test_legacy_purchase_alias_is_canonicalized():
    assert canonical_business_code("purchase") == "purchasing"
    assert canonical_business_code("purchases") == "purchasing"
