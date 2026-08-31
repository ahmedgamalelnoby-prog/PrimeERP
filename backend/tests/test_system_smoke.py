"""High-value architecture smoke tests for PrimeERP.

These tests intentionally validate boundaries that the previous CI did not cover:
- every importable backend module can be imported;
- SQLAlchemy mappers can be configured together;
- the users table has exactly one authoritative User model;
- the identity login route is actually registered in the FastAPI application.
"""

from __future__ import annotations

import importlib
import pkgutil

from fastapi import FastAPI
from sqlalchemy.orm import configure_mappers

import app.modules
from app.database.base import Base
from app.database.models import User
from app.modules.identity.models.user import User as IdentityUser
from main import app


def _iter_backend_modules() -> list[str]:
    names: list[str] = []
    for module_info in pkgutil.walk_packages(
        app.modules.__path__,
        prefix=f"{app.modules.__name__}.",
    ):
        name = module_info.name
        if ".tests" in name or name.endswith(".tests"):
            continue
        names.append(name)
    return names


def test_all_backend_modules_import() -> None:
    failures: list[str] = []

    for module_name in _iter_backend_modules():
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - failure diagnostics
            failures.append(f"{module_name}: {type(exc).__name__}: {exc}")

    assert not failures, "Backend module import failures:\n" + "\n".join(failures)


def test_sqlalchemy_mappers_are_consistent() -> None:
    configure_mappers()

    assert User is IdentityUser
    assert User.__tablename__ == "users"
    assert Base.metadata.tables["users"] is User.__table__


def test_identity_login_route_is_registered() -> None:
    assert isinstance(app, FastAPI)

    routes = {
        (method, route.path)
        for route in app.routes
        if hasattr(route, "methods")
        for method in route.methods
    }

    assert ("POST", "/api/v1/identity/login") in routes
    assert ("POST", "/api/v1/identity/refresh") in routes
