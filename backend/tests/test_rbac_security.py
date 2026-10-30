from types import SimpleNamespace

from app.core.permissions.checker import user_has_permission


def _user(**kwargs):
    defaults = {
        "is_platform_admin": False,
        "is_superuser": False,
        "role_id": None,
        "role": None,
        "permissions": [],
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class PermissionDatabase:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def scalar(self, statement):
        self.calls += 1
        return self.result


def test_platform_admin_bypasses_rbac_without_database_lookup():
    db = PermissionDatabase(None)
    assert user_has_permission(_user(is_platform_admin=True), "finance.post", db) is True
    assert db.calls == 0


def test_superuser_bypasses_rbac_without_database_lookup():
    db = PermissionDatabase(None)
    assert user_has_permission(_user(is_superuser=True), "finance.post", db) is True
    assert db.calls == 0


def test_role_permission_requires_active_database_grant():
    role = SimpleNamespace(permissions=[], is_active=True)
    db = PermissionDatabase(123)
    assert user_has_permission(_user(role_id=10, role=role), "finance.post", db) is True
    assert db.calls == 1


def test_inactive_or_revoked_permission_is_not_trusted_from_role():
    stale_role = SimpleNamespace(
        permissions=[SimpleNamespace(name="finance.post", code="finance.post", is_active=True)],
        is_active=True,
    )
    db = PermissionDatabase(None)
    assert user_has_permission(_user(role_id=10, role=stale_role), "finance.post", db) is False
    assert db.calls == 1


def test_missing_permission_denied_when_database_has_no_grant():
    role = SimpleNamespace(permissions=[], is_active=True)
    db = PermissionDatabase(None)
    assert user_has_permission(_user(role_id=10, role=role), "finance.post", db) is False
    assert db.calls == 1


def test_missing_role_denied_without_database_lookup():
    db = PermissionDatabase(123)
    assert user_has_permission(_user(), "finance.post", db) is False
    assert db.calls == 0
