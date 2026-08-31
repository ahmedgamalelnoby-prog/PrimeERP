"""High-value architecture smoke tests for PrimeERP.

These tests intentionally validate boundaries that the previous CI did not cover:
- every importable backend module can be imported;
- SQLAlchemy mappers can be configured together;
- the users table has exactly one authoritative User model;
- the identity login and refresh operations are exposed in the final API schema.
"""

from __future__ import annotations

import importlib
import pkgutil

from fastapi import FastAPI
from sqlalchemy.orm import configure_mappers

import app.modules as modules_pkg
from app.database.base import Base
from app.database.models import User
from app.modules.identity.api.router import router as identity_router
from app.modules.identity.models.user import User as IdentityUser
from main import app


def _iter_backend_modules() -> list[str]:
    names: list[str] = []
    for module_info in pkgutil.walk_packages(
        modules_pkg.__path__,
        prefix=f"{modules_pkg.__name__}.",
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


def test_identity_router_defines_login_and_refresh() -> None:
    routes = {
        (method, route.path)
        for route in identity_router.routes
        if hasattr(route, "methods")
        for method in route.methods
    }

    assert ("POST", "/login") in routes
    assert ("POST", "/refresh") in routes


def test_identity_auth_operations_are_in_openapi() -> None:
    assert isinstance(app, FastAPI)

    paths = app.openapi()["paths"]

    assert "/api/v1/identity/login" in paths
    assert "post" in paths["/api/v1/identity/login"]
    assert "/api/v1/identity/refresh" in paths
    assert "post" in paths["/api/v1/identity/refresh"]
