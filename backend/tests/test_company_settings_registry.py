import pytest

from app.modules.company_settings.registry import BY_KEY, CATALOG, validate_value


def test_company_policy_catalog_has_unique_keys_and_module_ownership():
    keys = [item["key"] for item in CATALOG]
    assert len(keys) == len(set(keys))
    assert all("." in item["key"] and item["module"] for item in CATALOG)


def test_negative_stock_policy_is_company_setting_and_disabled_by_default():
    assert BY_KEY["inventory.allow_negative_stock"]["default"] is False
    assert validate_value("inventory.allow_negative_stock", True) is True


def test_setting_validation_rejects_unknown_enum_values():
    with pytest.raises(ValueError):
        validate_value("hr.attendance_source", "random_device")


def test_setting_validation_rejects_wrong_boolean_type():
    with pytest.raises(ValueError):
        validate_value("inventory.allow_negative_stock", "true")


def test_setting_validation_bounds_fiscal_year_start_month():
    with pytest.raises(ValueError):
        validate_value("accounting.fiscal_year_start_month", 13)
