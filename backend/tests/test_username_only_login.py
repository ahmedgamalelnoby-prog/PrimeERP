from types import SimpleNamespace
from unittest.mock import MagicMock

from app.modules.identity.repositories.user_repository import UserRepository
from app.modules.identity.schemas.auth import LoginRequest


def test_login_request_requires_only_username_and_password():
    assert set(LoginRequest.model_fields) == {"login", "password"}
    payload = LoginRequest(login="employee01", password="secret")
    assert payload.login == "employee01"
    assert payload.password == "secret"


def test_login_lookup_uses_username_without_company_or_tenant_filter():
    user = SimpleNamespace(id=17, username="employee01")
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = [user]

    result = UserRepository().find_for_login(db, " Employee01 ")

    assert result == [user]
    statement = db.execute.call_args.args[0]
    sql = str(statement.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "lower(trim(users.username))" in sql
    assert "tenants" not in sql
    assert "users.tenant_id =" not in sql


def test_login_lookup_returns_multiple_legacy_matches_for_safe_rejection():
    users = [
        SimpleNamespace(id=1, username="employee01"),
        SimpleNamespace(id=2, username="employee01"),
    ]
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = users

    result = UserRepository().find_for_login(db, "employee01")

    assert result == users
    assert len(result) == 2
