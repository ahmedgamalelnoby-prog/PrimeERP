import pytest

from app.modules.company_settings.registry import BY_KEY, CATALOG, validate_value


def test_company_policy_catalog_has_unique_keys_and_module_ownership():
    keys = [item["key"] for item in CATALOG]
    assert len(keys) == len(set(keys))
    assert len(keys) == 71
    assert all("." in item["key"] and item["module"] for item in CATALOG)


@pytest.mark.parametrize("setting", CATALOG, ids=lambda item: item["key"])
def test_every_registered_default_passes_its_own_validator(setting):
    assert validate_value(setting["key"], setting["default"]) == setting["default"]


def test_only_options_with_a_verified_workflow_consumer_are_marked_runtime():
    runtime_keys = {item["key"] for item in CATALOG if item["status"] == "runtime"}
    assert runtime_keys == {
        "inventory.allow_negative_stock",
        "inventory.allow_below_cost_sale",
        "inventory.auto_reserve_sales_orders",
        "accounting.require_journal_approval",
        "general.default_language",
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
        "workflow.allow_self_approval",
        "inventory.require_bin_location",
        "general.branch_required",
        "accounting.period_lock_enabled",
        "sales.credit_limit_enforced",
        "purchasing.require_goods_receipt",
        "sales.default_payment_terms_days",
        "purchasing.default_payment_terms_days",
        "crm.duplicate_customer_check",
        "pos.allow_discount_without_approval",
        "pos.max_discount_pct_without_approval",
        "pos.require_shift_close",
        "inventory.require_warehouse",
        "inventory.expiry_tracking_required",
        "inventory.serial_tracking_default",
        "inventory.batch_tracking_default",
        "notifications.email_enabled",
        "notifications.whatsapp_enabled",
        "notifications.retry_limit",
        "tax.require_tax_code_on_invoice",
        "accounting.auto_post_sales_invoice",
        "accounting.auto_post_purchase_invoice",
        "accounting.default_receivable_account",
        "accounting.default_payable_account",
        "accounting.default_sales_account",
        "accounting.default_purchase_account",
        "accounting.default_cash_account",
        "purchasing.allow_invoice_price_variance",
        "purchasing.price_variance_tolerance_pct",
        "general.intercompany_enabled",
        "tax.einvoice_required_for_sales",
        "inventory.valuation_method",
        "sales.allow_negative_customer_balance",
        "sales.invoice_requires_delivery",
        "sales.allow_overbilling",
        "sales.require_order_approval",
        "sales.document_numbering",
        "sales.require_quote_approval",
        "general.require_project",
        "purchasing.require_purchase_order",
        "purchasing.require_purchase_approval",
        "hr.leave_requires_approval",
        "hr.allow_negative_leave_balance",
        "hr.require_attendance_approval",
        "hr.overtime_requires_approval",
        "hr.default_work_hours_per_day",
        "manufacturing.require_work_order",
        "manufacturing.allow_overproduction",
        "integrations.auto_sync_enabled",
    }


def test_policies_without_a_safe_workflow_consumer_remain_catalog_only():
    # These policies still lack complete owning workflows. Do not advertise them as enforced.
    catalog_only_keys = {
        "general.date_format",
        "hr.attendance_source",
        "hr.payroll_requires_approval",
        "hr.biometric_sync_interval_minutes",
        "workflow.approval_mode",
        "workflow.escalation_after_hours",
        "pos.allow_open_cash_drawer",
    }
    assert all(BY_KEY[key]["status"] == "catalog" for key in catalog_only_keys)


def test_below_cost_sale_policy_is_runtime_and_disabled_by_default():
    assert BY_KEY["inventory.allow_below_cost_sale"]["default"] is False
    assert BY_KEY["inventory.allow_below_cost_sale"]["status"] == "runtime"
    assert validate_value("inventory.allow_below_cost_sale", True) is True


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


@pytest.mark.parametrize("bad_format", ["DD-MM-YYYY", "YYYY/MM/DD", "", None, True])
def test_company_date_format_accepts_only_declared_formats(bad_format):
    with pytest.raises(ValueError):
        validate_value("general.date_format", bad_format)


@pytest.mark.parametrize("valid_format", ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"])
def test_company_date_format_accepts_declared_formats(valid_format):
    assert validate_value("general.date_format", valid_format) == valid_format


@pytest.mark.parametrize("bad_value", [-0.01, 100.01, float("nan"), float("inf"), True, "5"])
def test_purchase_price_variance_tolerance_rejects_out_of_range_values(bad_value):
    with pytest.raises(ValueError):
        validate_value("purchasing.price_variance_tolerance_pct", bad_value)


@pytest.mark.parametrize("bad_limit", [-1, 6, True, 1.5])
def test_notification_retry_limit_is_bounded(bad_limit):
    with pytest.raises(ValueError):
        validate_value("notifications.retry_limit", bad_limit)


def test_notification_delivery_switches_default_to_disabled():
    assert BY_KEY["notifications.email_enabled"]["default"] is False
    assert BY_KEY["notifications.whatsapp_enabled"]["default"] is False
    assert BY_KEY["notifications.email_enabled"]["status"] == "runtime"
    assert BY_KEY["notifications.whatsapp_enabled"]["status"] == "runtime"
