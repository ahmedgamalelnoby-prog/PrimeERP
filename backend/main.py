from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.router import build_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RequestContextMiddleware
from app.core.module_engine.bootstrap import bootstrap_module_registry
from app.core.module_engine.registry import ModuleRegistry
from app.core.security.production import validate_production_configuration
from app.database import models as database_models  # noqa: F401
from app.database.session import SessionLocal


def create_application() -> FastAPI:
    """Build a fresh PrimeERP application with an isolated API router tree."""
    if settings.ENVIRONMENT.strip().lower() == "production":
        validate_production_configuration()

    module_registry: ModuleRegistry = bootstrap_module_registry()
    docs_enabled = settings.ENVIRONMENT.strip().lower() != "production" or settings.DEBUG

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
    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Idempotency-Key"],
        expose_headers=["X-Request-ID"],
    )

    application.include_router(build_router(), prefix=settings.API_V1_STR)

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
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return JSONResponse(
                content={
                    "success": True,
                    "message": "Service is healthy.",
                    "data": {"status": "healthy", "database": "ready", "service": settings.APP_NAME, "version": settings.APP_VERSION},
                }
            )
        except Exception:
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "message": "Service is not ready.",
                    "data": {"status": "unhealthy", "database": "unavailable", "service": settings.APP_NAME, "version": settings.APP_VERSION},
                },
            )
        finally:
            db.close()

    @application.get("/modules", tags=["System"])
    async def module_inventory() -> JSONResponse:
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
        return JSONResponse(content={"success": True, "data": {"count": len(modules), "modules": modules}})

    return application


app = create_application()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=settings.DEBUG, log_level="info")
