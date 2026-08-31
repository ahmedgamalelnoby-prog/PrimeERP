from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.context import get_request_context
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RequestContextMiddleware

# استيراد الموديلات لضمان تسجيلها داخل SQLAlchemy metadata
from app.database import models as database_models  # noqa: F401


def _has_route(application: FastAPI, method: str, path: str) -> bool:
    """Return True when an exact API route is already registered."""
    return any(
        isinstance(route, APIRoute)
        and route.path == path
        and method.upper() in route.methods
        for route in application.routes
    )


def _ensure_identity_routes(application: FastAPI) -> None:
    """Ensure the canonical identity auth endpoints are mounted exactly once.

    The API v1 router is the primary registration point.  The explicit guard
    below makes application startup resilient to import-order/circular-import
    situations while preventing duplicate route registration.
    """
    required_routes = (
        ("POST", "/api/v1/identity/login"),
        ("POST", "/api/v1/identity/refresh"),
        ("GET", "/api/v1/identity/me"),
    )

    if all(_has_route(application, method, path) for method, path in required_routes):
        return

    from app.modules.identity.api.router import router as identity_router

    application.include_router(
        identity_router,
        prefix=f"{settings.API_V1_STR}/identity",
        tags=["identity"],
    )


def create_application() -> FastAPI:
    """
    Create and configure the PrimeERP FastAPI application.
    """

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="PrimeERP - نظام إدارة المؤسسات",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # تسجيل معالجات الأخطاء
    register_exception_handlers(application)

    # يتم تسجيل Request Context أولًا.
    application.add_middleware(RequestContextMiddleware)

    # يتم تسجيل CORS بعده حتى يكون الطبقة الخارجية
    # ويضيف CORS Headers حتى عند حدوث أخطاء.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    application.include_router(
        api_v1_router,
        prefix=settings.API_V1_STR,
    )

    # Identity auth is a core platform capability. Ensure its canonical
    # endpoints exist once even if router import order changes.
    _ensure_identity_routes(application)

    return application


app = create_application()


@app.get("/", tags=["System"])
async def root() -> JSONResponse:
    return JSONResponse(
        content={
            "success": True,
            "message": f"Welcome to {settings.APP_NAME} API",
            "data": {
                "version": settings.APP_VERSION,
                "status": "online",
                "docs": "/docs",
                "redoc": "/redoc",
            },
        }
    )


@app.get("/health", tags=["System"])
async def health_check() -> JSONResponse:
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


@app.get("/debug/request-context", tags=["System"])
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


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
        log_level="info",
    )
