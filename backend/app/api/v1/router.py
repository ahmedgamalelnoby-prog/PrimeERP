from fastapi import APIRouter

from app.modules.identity.api.router import router as identity_router
from app.modules.saas.router import router as saas_router
from app.modules.transactions.api.router import router as transactions_router
from app.modules.accounting.fiscal_years.api.router import router as fiscal_years_router
from app.modules.platform.features.router import router as features_router
from app.modules.platform.plans.router import router as plans_router
from app.modules.platform.tenants.router import router as tenants_router
from app.modules.platform.saas_router import router as platform_saas_router
from app.modules.legal.router import router as legal_router

router = APIRouter()

router.include_router(identity_router, prefix="/identity", tags=["identity"])
router.include_router(features_router)
router.include_router(saas_router, prefix="/saas", tags=["saas"])
router.include_router(platform_saas_router)
router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
router.include_router(fiscal_years_router, prefix="/accounting/fiscal-years", tags=["accounting-fiscal-years"])
router.include_router(plans_router)
router.include_router(tenants_router, prefix="/platform")
router.include_router(legal_router)
