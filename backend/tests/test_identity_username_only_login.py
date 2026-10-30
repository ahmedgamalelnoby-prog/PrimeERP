from pathlib import Path
from types import SimpleNamespace

from app.modules.identity.services.authentication_service import AuthenticationService


ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_password_match_resolves_exactly_one_tenant_identity(monkeypatch):
    monkeypatch.setattr(
        "app.modules.identity.services.authentication_service.password_service.verify_password",
        lambda password, hashed: password == "correct-password" and hashed == "tenant-a-hash",
    )
    users = [
        SimpleNamespace(id=1, tenant_id=10, hashed_password="tenant-a-hash"),
        SimpleNamespace(id=2, tenant_id=20, hashed_password="tenant-b-hash"),
    ]

    matches = AuthenticationService._matching_users_by_password(
        users,
        "correct-password",
    )

    assert len(matches) == 1
    assert matches[0].tenant_id == 10


def test_password_match_does_not_choose_between_ambiguous_duplicate_accounts(monkeypatch):
    monkeypatch.setattr(
        "app.modules.identity.services.authentication_service.password_service.verify_password",
        lambda password, hashed: password == "same-password",
    )
    users = [
        SimpleNamespace(id=1, tenant_id=10, hashed_password="hash-a"),
        SimpleNamespace(id=2, tenant_id=20, hashed_password="hash-b"),
    ]

    matches = AuthenticationService._matching_users_by_password(
        users,
        "same-password",
    )

    assert len(matches) == 2


def test_wrong_password_matches_no_tenant_identity(monkeypatch):
    monkeypatch.setattr(
        "app.modules.identity.services.authentication_service.password_service.verify_password",
        lambda password, hashed: password == "correct-password",
    )
    users = [
        SimpleNamespace(id=1, tenant_id=10, hashed_password="hash-a"),
        SimpleNamespace(id=2, tenant_id=20, hashed_password="hash-b"),
    ]

    assert AuthenticationService._matching_users_by_password(
        users,
        "wrong-password",
    ) == []


def test_login_resolves_company_from_unique_password_match_without_company_input():
    auth = source("app/modules/identity/services/authentication_service.py")
    schema = source("app/modules/identity/schemas/auth.py")
    assert "_matching_users_by_password(" in auth
    assert "if len(matching_users) != 1:" in auth
    assert "company_name_required" not in auth
    assert "tenant_name" not in schema
    assert "tenant_slug" not in schema


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
    auth_service = source("../frontend/src/modules/identity/services/authentication.service.ts")
    auth_types = source("../frontend/src/modules/identity/types/auth.ts")
    auth_context = source("../frontend/src/modules/identity/context/AuthContext.tsx")
    assert "companyName" not in page
    assert "tenantSlug" not in form
    assert "tenantSlug" not in hook
    assert "tenant_slug" not in auth_service
    assert "tenant_name" not in auth_service
    assert "tenant_slug" not in auth_types
    assert "tenant_name" not in auth_types
    assert "tenantSlug" not in auth_context
    assert "tenantName" not in auth_context
