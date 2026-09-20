from __future__ import annotations

import sys
import traceback
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"

REQUIRED_FILES = (
    ".env.docker.example",
    "docker-compose.yml",
    "backend/Dockerfile",
    "frontend/Dockerfile",
    "frontend/nginx.conf",
    "backend/scripts/check_api_security.py",
    "backend/scripts/check_production_config.py",
    "backend/app/modules/integrations/salla_service.py",
    "backend/app/modules/integrations/salla_sync.py",
    "backend/app/modules/integrations/salla_shipping_service.py",
)

REQUIRED_SERVICES = {"db", "migrate", "backend", "frontend"}

# This is the release contract. These are the canonical runtime paths after
# the /api/v1 prefix is mounted by backend/main.py. Keep this list aligned
# with the public module API, not with the source-file layout: router prefixes
# are intentionally distributed between module routers and the v1 aggregator.
REQUIRED_API_CONTRACT = {
    "/api/v1/identity/login": {"POST"},
    "/api/v1/identity/me": {"GET"},
    "/api/v1/platform/tenants": {"GET", "POST"},
    "/api/v1/subscriptions/tenant/{tenant_id}": {"GET"},
    "/api/v1/accounting/tax-rates": {"GET", "POST"},
    "/api/v1/taxes/rates": {"GET", "POST"},
    "/api/v1/uom": {"GET", "POST"},
    "/api/v1/inventory/items": {"GET", "POST"},
    "/api/v1/inventory/items/{item_id}/stock": {"GET"},
    "/api/v1/integrations/connections": {"GET", "POST"},
    "/api/v1/shipping/carriers": {"GET", "POST"},
}


def fail(message: str) -> None:
    raise SystemExit(f"RELEASE READINESS FAILED: {message}")


def main() -> int:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file():
            fail(f"required file is missing: {relative}")

    compose_path = ROOT / "docker-compose.yml"
    compose = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    if not isinstance(compose, dict):
        fail("docker-compose.yml is not a YAML mapping")

    services = compose.get("services")
    if not isinstance(services, dict) or not REQUIRED_SERVICES.issubset(services):
        fail(f"compose services must include: {sorted(REQUIRED_SERVICES)}")

    db = services["db"]
    if db.get("ports"):
        fail("PostgreSQL must not be exposed directly by the production compose file")
    if "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}" not in str(db.get("environment", {})):
        fail("database password must be required at compose evaluation time")

    for service_name in ("migrate", "backend"):
        environment = str(services[service_name].get("environment", {}))
        if "${SECRET_KEY:?SECRET_KEY must be set}" not in environment:
            fail(f"{service_name} must require SECRET_KEY")
        if "${CORS_ORIGINS:?CORS_ORIGINS must be set}" not in environment:
            fail(f"{service_name} must require CORS_ORIGINS")

    migrate = services["migrate"]
    if migrate.get("restart") != "no" or migrate.get("command") != ["alembic", "upgrade", "head"]:
        fail("migration service must be a one-shot alembic upgrade head job")

    backend = services["backend"]
    if backend.get("depends_on", {}).get("migrate", {}).get("condition") != "service_completed_successfully":
        fail("backend must start only after successful migrations")
    if "healthcheck" not in backend:
        fail("backend healthcheck is required")

    backend_dockerfile = (ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
    if "USER appuser" not in backend_dockerfile:
        fail("backend container must run as non-root appuser")
    if "HEALTHCHECK" not in backend_dockerfile:
        fail("backend image healthcheck is required")

    frontend_dockerfile = (ROOT / "frontend/Dockerfile").read_text(encoding="utf-8")
    if "FROM nginx:" not in frontend_dockerfile or "HEALTHCHECK" not in frontend_dockerfile:
        fail("frontend must use a production nginx stage with a healthcheck")

    # Route contract is verified from FastAPI's registered OpenAPI route map.
    # A source-text search is deliberately not used here because a router's
    # prefix may live in a child module while its endpoint lives in another
    # file; source matching therefore produced false failures in CI.
    try:
        sys.path.insert(0, str(BACKEND))
        from main import create_application

        application = create_application()
        paths = application.openapi().get("paths", {})
    except Exception as exc:
        traceback.print_exc()
        fail(f"FastAPI application could not be constructed for route audit: {type(exc).__name__}: {exc}")

    missing_paths = [path for path in REQUIRED_API_CONTRACT if path not in paths]
    if missing_paths:
        fail(f"required registered API routes are missing: {missing_paths}")

    method_mismatches = []
    for path, required_methods in REQUIRED_API_CONTRACT.items():
        registered_methods = {
            method.upper()
            for method in paths[path]
            if method.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
        }
        missing_methods = required_methods - registered_methods
        if missing_methods:
            method_mismatches.append(
                f"{path}: missing methods {sorted(missing_methods)}; registered {sorted(registered_methods)}"
            )
    if method_mismatches:
        fail(f"registered API method contract mismatch: {method_mismatches}")

    print("Release readiness static, runtime route and Docker contract audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
