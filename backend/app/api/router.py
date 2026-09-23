from fastapi import APIRouter

from app.api.v1.router import build_router as build_v1_router


def build_router() -> APIRouter:
    """Build the complete API router tree for one application instance."""
    router = APIRouter()
    router.include_router(build_v1_router())
    return router
