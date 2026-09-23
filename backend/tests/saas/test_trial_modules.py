from app.modules.saas.trial_modules import CORE_TRIAL_MODULES, trial_modules_for_business


def test_trial_business_matrix_is_not_full_catalog():
    allowed = trial_modules_for_business("other")
    assert allowed == CORE_TRIAL_MODULES
    assert "treasury" not in allowed
    assert "integrations" not in allowed
    assert "enterprise" not in allowed


def test_restaurant_trial_includes_restaurant_operations_only():
    allowed = trial_modules_for_business("restaurant")
    assert {"accounting", "sales", "inventory", "purchasing", "restaurant", "pos", "reports"}.issubset(allowed)
    assert "treasury" not in allowed
    assert "manufacturing" not in allowed
    assert "shipping" not in allowed


def test_retail_trial_includes_retail_operations_and_shipping():
    allowed = trial_modules_for_business("retail")
    assert {"accounting", "sales", "inventory", "purchasing", "crm", "pos", "shipping", "reports"}.issubset(allowed)
    assert "restaurant" not in allowed
    assert "manufacturing" not in allowed


def test_unknown_business_type_fails_closed_to_core_trial_set():
    assert trial_modules_for_business("not-a-real-business") == CORE_TRIAL_MODULES
