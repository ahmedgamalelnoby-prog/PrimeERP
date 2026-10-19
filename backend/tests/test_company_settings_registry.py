import pytest

from app.modules.company_settings.registry import BY_KEY, CATALOG, validate_value


def test_company_policy_catalog_has_unique_keys_and_module_ownership():
    keys = [item["key"] for item in CATALOG]
    assert len(keys) == len(set(keys))
    assert len(keys) == 68
    assert all("." in item["key"] and item["module"] for item in CATALOG)


@pytest.mark.parametrize("setting", CATALOG, ids=lambda item: item["key"])
def test_every_registered_default_passes_its_own_validator(setting):
    assert validate_value(setting["key"], setting["default"]) == setting["default"]


def test_only_options_with_a_verified_workflow_consumer_are_marked_runtime():
    runtime_keys = {item["key"] for item in CATALOG if item["status"] == "runtime"}
    assert runtime_keys == {
        "inventory.allow_negative_stock",
        "accounting.require_journal_approval",
        "general.timezone",
        "general.base_currency",
        "general.allow_multi_currency",
        "general.require_cost_center",
        "accounting.allow_backdated_entries",
        "integrations.retry_limit",
        "integrations.webhook_signature_required",
        "accounting.rounding_method",
        "accounting.fiscal_year_start_month",
        "tax.default_tax_inclusive_pricing",
        "inventory.require_bin_location",
        "workflow.allow_self_approval",
    }


def test_negative_stock_policy_is_company_setting_and_disabled_by_default():
    assert BY_KEY["inventory.allow_negative_stock"]["default"] is False
    assert validate_value("inventory.allow_negative_stock", True) is True


@pytest.mark.parametrize("bad_value", ["random_device", "biometric_clock_xyz", None, True])
def test_setting_validation_rejects_unknown_enum_values(bad_value):
    with pytest.raises(ValueError):
        validate_value("hr.attendance_source", bad_value)


@pytest.mark.parametrize("bad_value", ["true", 1, None])
def test_setting_validation_rejects_non_boolean_values(bad_value):
    with pytest.raises(ValueError):
        validate_value("inventory.allow_negative_stock", bad_value)


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), float("-inf"), True, "3"])
def test_setting_validation_rejects_non_finite_or_non_numeric_values(bad_value):
    with pytest.raises(ValueError):
        validate_value("hr.default_work_hours_per_day", bad_value)


@pytest.mark.parametrize("bad_month", [0, 13, True, 1.5])
def test_setting_validation_bounds_fiscal_year_start_month(bad_month):
    with pytest.raises(ValueError):
        validate_value("accounting.fiscal_year_start_month", bad_month)


@pytest.mark.parametrize("bad_timezone", ["Mars/Olympus", "", None, 3])
def test_setting_validation_rejects_invalid_timezones(bad_timezone):
    with pytest.raises(ValueError):
        validate_value("general.timezone", bad_timezone)


@pytest.mark.parametrize("bad_currency", ["egp", "EG", "EGPX", "EGP/ USD", "", None])
def test_setting_validation_rejects_invalid_currency_codes(bad_currency):
    with pytest.raises(ValueError):
        validate_value("general.base_currency", bad_currency)


def test_setting_validation_rejects_unknown_keys():
    with pytest.raises(ValueError):
        validate_value("custom.customer_specific_setting", True)


def test_setting_validation_rejects_unreasonable_workday_length():
    for value in (0, -1, 24.01, 100):
        with pytest.raises(ValueError):
            validate_value("hr.default_work_hours_per_day", value)


def test_journal_approval_policy_defaults_to_required():
    assert BY_KEY["accounting.require_journal_approval"]["default"] is True
    assert BY_KEY["accounting.require_journal_approval"]["status"] == "runtime"
    assert validate_value("accounting.require_journal_approval", False) is False
