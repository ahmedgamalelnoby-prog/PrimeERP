from fastapi import APIRouter

from app.modules.accounting.fiscal_years.api.router import router as fiscal_years_router
from app.modules.identity.api.router import router as identity_router
from app.modules.legal.router import router as legal_router
from app.modules.platform.billing_router import router as billing_router
from app.modules.platform.features.router import router as features_router
from app.modules.platform.plans.router import router as plans_router
from app.modules.platform.promotions_router import router as promotions_router
from app.modules.platform.saas_router import router as platform_saas_router
from app.modules.platform.tenants.router import router as tenants_router
from app.modules.saas.router import router as saas_router
from app.modules.transactions.api.router import router as transactions_router


def build_router() -> APIRouter:
    """Build a fresh API v1 router for each application instance."""
    api_router = APIRouter()

    api_router.include_router(
        identity_router,
        prefix="/identity",
        tags=["identity"],
    )
    api_router.include_router(features_router)
    api_router.include_router(
        saas_router,
        prefix="/saas",
        tags=["saas"],
    )
    api_router.include_router(platform_saas_router)
    api_router.include_router(billing_router)
    api_router.include_router(promotions_router)
    api_router.include_router(
        transactions_router,
        prefix="/transactions",
        tags=["transactions"],
    )
    api_router.include_router(
        fiscal_years_router,
        prefix="/accounting/fiscal-years",
        tags=["accounting-fiscal-years"],
    )
    api_router.include_router(plans_router)
    api_router.include_router(
        tenants_router,
        prefix="/platform",
    )
    api_router.include_router(legal_router)

    return api_router


# Backwards-compatible module-level router for code that imports it directly.
# Production application instances use build_router() so router state is fresh.
router = build_router()
