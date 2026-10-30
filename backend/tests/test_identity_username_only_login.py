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
    login_schema = schema.split("class RefreshTokenRequest", 1)[0]
    assert "_matching_users_by_password(" in auth
    assert "if len(matching_users) != 1:" in auth
    assert "company_name_required" not in auth
    assert "tenant_name" not in login_schema
    assert "tenant_slug" not in login_schema


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


def test_authenticated_user_cannot_override_tenant_context():
    dependency = source("app/modules/identity/dependencies/current_user.py")
    assert "user.tenant_id != token_tenant_id" in dependency
    assert "requested_tenant_id != user.tenant_id" in dependency
    assert "Tenant context does not match the authenticated user" in dependency


def test_company_reads_are_scoped_to_authenticated_tenant():
    companies = source("app/modules/companies/router.py")
    assert "Company.tenant_id == _tenant_id(user)" in companies
    assert "Company.tenant_id == _tenant_id(current_user)" in companies
    assert "return _get_company(db, company_id, current_user)" in companies


def test_refresh_token_revalidates_user_and_tenant_before_issuing_new_tokens():
    auth = source("app/modules/identity/services/authentication_service.py")
    refresh = auth.split("def refresh(", 1)[1].split("def _matching_users_by_password", 1)[0]
    assert "user_repository.get_by_id(db=db, user_id=record.user_id)" in refresh
    assert "self._validate_user(user)" in refresh
    assert "self._get_auth_tenant(db, user.tenant_id)" in refresh
    assert "self._ensure_subscription_allows_login(tenant, subscription)" in refresh


def test_revoked_permission_is_not_granted_from_stale_loaded_role_relationship():
    from app.core.permissions.checker import user_has_permission

    stale_permission = SimpleNamespace(name="users.write", code="users.write", is_active=True)
    stale_role = SimpleNamespace(is_active=True, permissions=[stale_permission])
    user = SimpleNamespace(
        is_platform_admin=False,
        is_superuser=False,
        role_id=7,
        role=stale_role,
        permissions=[],
    )

    class RevokedPermissionDatabase:
        @staticmethod
        def scalar(statement):
            return None

    assert user_has_permission(user, "users.write", RevokedPermissionDatabase()) is False


def test_active_permission_is_confirmed_from_database():
    from app.core.permissions.checker import user_has_permission

    user = SimpleNamespace(
        is_platform_admin=False,
        is_superuser=False,
        role_id=7,
        role=SimpleNamespace(is_active=True, permissions=[]),
        permissions=[],
    )

    class ActivePermissionDatabase:
        @staticmethod
        def scalar(statement):
            return 123

    assert user_has_permission(user, "users.write", ActivePermissionDatabase()) is True


def test_username_rename_checks_all_other_legacy_records_not_only_first_match():
    users = source("app/modules/identity/services/user_service.py")
    update = users.split("def update_user(", 1)[1]
    assert "duplicate_user_id = db.scalar(" in update
    assert "func.lower(User.username) == new_username" in update
    assert "User.id != user.id" in update
    assert "repository.get_by_username(db, new_username" not in update


def test_role_delegation_uses_database_permission_sets_not_stale_relationships():
    users = source("app/modules/identity/services/user_service.py")
    block = users.split("def _validate_role_assignment", 1)[1].split("def _resolve_write_tenant_id", 1)[0]
    assert "select(Role.is_active).where(Role.id == role_id)" in block
    assert "select(Role.is_active).where(Role.id == current_role_id)" in block
    assert "select(Permission.name)" in block
    assert "role_permissions.c.role_id == selected_role_id" in block
    assert "getattr(current_role, \"permissions\"" not in block
    assert "getattr(target_role, \"permissions\"" not in block


def test_branch_update_schema_cannot_reassign_branch_to_another_company():
    schema = source("app/modules/branches/schemas.py")
    update_schema = schema.split("class BranchUpdate", 1)[1].split("class BranchResponse", 1)[0]
    assert "company_id" not in update_schema
    router = source("app/modules/branches/router.py")
    assert "def _branch(db: Session, branch_id: int, user: User)" in router
    assert "Branch.tenant_id == _tenant_id(user)" in router

def test_user_restore_service_is_implemented_and_tenant_scoped():
    users = source("app/modules/identity/services/user_service.py")
    restore = users.split("def restore_user(", 1)[1].split("def list_users(", 1)[0]
    assert "include_deleted=True" in restore
    assert "for_update=True" in restore
    assert "_resolve_write_tenant_id(tenant_id)" in restore
    assert "pg_advisory_xact_lock" in restore
    assert "repository.restore(db, user)" in restore
    assert 'user.is_active = False' in restore
    assert "must not silently grant access" in restore
    assert 'action="user.restore"' in restore


def test_user_restore_rejects_username_and_tenant_email_conflicts():
    users = source("app/modules/identity/services/user_service.py")
    restore = users.split("def restore_user(", 1)[1].split("def list_users(", 1)[0]
    assert "duplicate_username_id = db.scalar(" in restore
    assert "func.lower(User.username) == user.username.strip().lower()" in restore
    assert "duplicate_email_id = db.scalar(" in restore
    assert "User.tenant_id == user.tenant_id" in restore
    assert "func.lower(User.email) == user.email.strip().lower()" in restore
