from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.router import build_router
from app.core.config import settings
from app.core.context import get_request_context
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from app.core.module_engine.bootstrap import bootstrap_module_registry
from app.core.module_engine.registry import ModuleRegistry
from app.database import models as database_models  # noqa: F401
from app.database.session import SessionLocal
from app.modules.identity.api.router import router as identity_router


def create_application() -> FastAPI:
    """Build a fresh PrimeERP application with an isolated API router tree."""
    module_registry: ModuleRegistry = bootstrap_module_registry()
    docs_enabled = settings.APP_ENV != "production"

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="PrimeERP - نظام إدارة المؤسسات",
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if docs_enabled else None,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
    )
    application.state.module_registry = module_registry

    register_exception_handlers(application)
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    api_router = build_router()
    # Keep the authentication boundary present even if a future modular router
    # catalog omits the identity router. The guard prevents duplicate routes.
    if not any(route.path == "/identity/login" for route in api_router.routes):
        api_router.include_router(identity_router, prefix="/identity", tags=["identity"])
    application.include_router(api_router, prefix=settings.API_V1_STR)

    @application.get("/", tags=["System"])
    async def root() -> JSONResponse:
        return JSONResponse(
            content={
                "success": True,
                "message": f"Welcome to {settings.APP_NAME} API",
                "data": {
                    "version": settings.APP_VERSION,
                    "status": "online",
                    "docs": "/docs" if docs_enabled else None,
                    "redoc": "/redoc" if docs_enabled else None,
                },
            }
        )

    @application.get("/health", tags=["System"])
    async def health_check() -> JSONResponse:
        """Liveness probe: confirms that the application process is running."""
        return JSONResponse(
            content={
                "success": True,
                "message": "Service is healthy.",
                "data": {
                    "status": "healthy",
                    "service": settings.APP_NAME,
                    "version": settings.APP_VERSION,
                },
            }
        )

    @application.get("/ready", tags=["System"])
    async def readiness_check() -> JSONResponse:
        """Readiness probe: confirms that the application can reach its database."""
        try:
            with SessionLocal() as db:
                db.execute(text("SELECT 1"))
        except Exception:
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "message": "Service is not ready.",
                    "data": {"status": "not_ready"},
                },
            )
        return JSONResponse(
            content={
                "success": True,
                "message": "Service is ready.",
                "data": {"status": "ready"},
            }
        )

    @application.get("/modules", tags=["System"])
    async def module_inventory() -> JSONResponse:
        """Return the platform module inventory without exposing tenant secrets."""
        modules = []
        for manifest in sorted(module_registry.all(), key=lambda item: item.key):
            state = module_registry.state(manifest.key)
            modules.append(
                {
                    "technical_name": manifest.key,
                    "display_name": manifest.display_name,
                    "version": manifest.version,
                    "domain": manifest.domain,
                    "dependencies": list(manifest.dependencies),
                    "installable": manifest.installable,
                    "installed": state.installed,
                    "enabled": state.enabled,
                }
            )
        return JSONResponse(
            content={
                "success": True,
                "data": {"count": len(modules), "modules": modules},
            }
        )

    if settings.DEBUG:
        @application.get("/debug/request-context", tags=["System"])
        async def debug_request_context() -> dict:
            context = get_request_context()
            return {
                "success": True,
                "data": {
                    "request_id": context.request_id,
                    "ip_address": context.ip_address,
                    "user_agent": context.user_agent,
                    "language": context.language,
                    "timezone": context.timezone,
                    "user_id": context.user_id,
                    "tenant_id": context.tenant_id,
                    "company_id": context.company_id,
                    "branch_id": context.branch_id,
                },
            }

    return application


app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
        log_level="info",
    )
