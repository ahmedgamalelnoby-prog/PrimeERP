from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import build_router
from app.core.config import settings
from app.core.context import get_request_context
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RequestContextMiddleware
from app.database import models as database_models  # noqa: F401


def create_application() -> FastAPI:
    """Build a fresh PrimeERP application with an isolated API router tree."""
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="PrimeERP - نظام إدارة المؤسسات",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    register_exception_handlers(application)
    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # The application boundary owns exactly one router tree.
    application.include_router(
        build_router(),
        prefix=settings.API_V1_STR,
    )

    @application.get("/", tags=["System"])
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

    @application.get("/health", tags=["System"])
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
