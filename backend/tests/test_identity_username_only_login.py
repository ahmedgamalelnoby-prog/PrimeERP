from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_login_resolves_company_from_unique_password_match_without_company_input():
    auth = source("app/modules/identity/services/authentication_service.py")
    schema = source("app/modules/identity/schemas/auth.py")
    assert "matching_users = [" in auth
    assert "candidate.hashed_password" in auth
    assert "if len(matching_users) != 1:" in auth
    assert "company_name_required" not in auth
    assert "tenant_name: Optional[str] = Field(" in schema
    assert "default=None" in schema


def test_user_creation_and_rename_reserve_username_across_tenants():
    users = source("app/modules/identity/services/user_service.py")
    assert users.count("pg_advisory_xact_lock") >= 2
    assert "get_by_username(db, normalized_username, include_deleted=True)" in users
    assert "get_by_username(db, new_username, include_deleted=True)" in users
    assert "unique username across PrimeERP" in users


def test_trial_registration_reserves_global_username_before_creating_tenant_owner():
    saas = source("app/modules/saas/service.py")
    assert "primeerp:username:{normalized_username}" in saas
    assert "func.lower(User.username) == normalized_username" in saas
    assert saas.index("pg_advisory_xact_lock") < saas.index("def register_trial_tenant")


def test_both_login_forms_do_not_request_company_or_tenant_identifier():
    page = source("../frontend/src/modules/identity/pages/LoginPage.tsx")
    form = source("../frontend/src/modules/identity/components/LoginForm.tsx")
    hook = source("../frontend/src/modules/identity/hooks/useLogin.ts")
    assert "companyName" not in page
    assert "tenantSlug" not in form
    assert "tenantSlug" not in hook
