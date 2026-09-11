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


def _permission(name: str, active: bool = True):
    return SimpleNamespace(name=name, is_active=active)


def test_platform_admin_bypasses_rbac():
    assert user_has_permission(_user(is_platform_admin=True), "finance.post") is True


def test_superuser_bypasses_rbac():
    assert user_has_permission(_user(is_superuser=True), "finance.post") is True


def test_role_permission_allows_active_permission():
    role = SimpleNamespace(
        permissions=[_permission("finance.post")],
        is_active=True,
    )
    assert user_has_permission(_user(role_id=10, role=role), "finance.post") is True


def test_inactive_permission_is_not_trusted_from_role():
    role = SimpleNamespace(
        permissions=[_permission("finance.post", active=False)],
        is_active=True,
    )
    assert user_has_permission(_user(role_id=10, role=role), "finance.post") is False


def test_missing_permission_denied_without_database_lookup():
    role = SimpleNamespace(
        permissions=[_permission("finance.read")],
        is_active=True,
    )
    assert user_has_permission(_user(role_id=10, role=role), "finance.post") is False
