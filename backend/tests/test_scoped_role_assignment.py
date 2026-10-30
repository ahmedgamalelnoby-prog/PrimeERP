from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.permissions import checker


class _ScalarRows:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


def _db_with_roles(target_active=True, actor_active=True, target_permissions=(), actor_permissions=()):
    db = MagicMock()
    db.get.side_effect = lambda model, role_id: SimpleNamespace(
        id=role_id,
        is_active=target_active if role_id == 20 else actor_active,
    )
    db.scalars.side_effect = [
        _ScalarRows(list(target_permissions)),
        _ScalarRows(list(actor_permissions)),
    ]
    return db


def test_role_assignment_allows_only_permission_subset(monkeypatch):
    monkeypatch.setattr(checker, "effective_role_id", lambda user, db: 10)
    db = _db_with_roles(
        target_permissions={"company.access", "inventory.access"},
        actor_permissions={"company.access", "inventory.access", "inventory.write"},
    )

    assert checker.can_assign_role(SimpleNamespace(id=1), 20, db) is True


def test_role_assignment_rejects_permission_escalation(monkeypatch):
    monkeypatch.setattr(checker, "effective_role_id", lambda user, db: 10)
    db = _db_with_roles(
        target_permissions={"company.access", "accounting.post"},
        actor_permissions={"company.access"},
    )

    assert checker.can_assign_role(SimpleNamespace(id=1), 20, db) is False


def test_role_assignment_rejects_inactive_target_role(monkeypatch):
    monkeypatch.setattr(checker, "effective_role_id", lambda user, db: 10)
    db = _db_with_roles(target_active=False)

    assert checker.can_assign_role(SimpleNamespace(id=1), 20, db) is False
    db.scalars.assert_not_called()


def test_role_assignment_rejects_actor_without_effective_role(monkeypatch):
    monkeypatch.setattr(checker, "effective_role_id", lambda user, db: None)
    db = _db_with_roles()

    assert checker.can_assign_role(SimpleNamespace(id=1), 20, db) is False
    db.scalars.assert_not_called()


@pytest.mark.parametrize("is_platform_admin,is_superuser", [(True, False), (False, True)])
def test_platform_authorities_can_assign_active_role(is_platform_admin, is_superuser):
    db = _db_with_roles()
    user = SimpleNamespace(is_platform_admin=is_platform_admin, is_superuser=is_superuser)

    assert checker.can_assign_role(user, 20, db) is True
    db.scalars.assert_not_called()
