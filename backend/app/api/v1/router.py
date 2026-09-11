from fastapi import APIRouter

from app.modules.accounting.fiscal_years.api.router import router as fiscal_years_router
from app.modules.accounting.journals.api.journal_entries import router as journal_entries_router
from app.modules.accounting.reports.router import router as financial_reports_router
from app.modules.identity.api.router import router as identity_router
from app.modules.inventory.items.router import router as inventory_items_router
from app.modules.inventory.locations.router import router as inventory_locations_router
from app.modules.inventory.warehouses.router import router as inventory_warehouses_router
from app.modules.legal.router import router as legal_router
from app.modules.platform.features.router import router as features_router
from app.modules.platform.plans.router import router as plans_router
from app.modules.platform.subscriptions.router import router as subscriptions_router
from app.modules.platform.tenants.router import router as tenants_router
from app.modules.saas.router import router as saas_router
from app.modules.transactions.api.router import router as transactions_router


def build_router() -> APIRouter:
    """Build an isolated API v1 router tree for one application instance."""
    api_router = APIRouter()
    api_router.include_router(identity_router, prefix="/identity", tags=["identity"])
    api_router.include_router(features_router)
    api_router.include_router(saas_router, prefix="/saas", tags=["saas"])
    api_router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
    api_router.include_router(fiscal_years_router, prefix="/accounting/fiscal-years", tags=["accounting-fiscal-years"])
    api_router.include_router(journal_entries_router)
    api_router.include_router(financial_reports_router)
    api_router.include_router(inventory_items_router)
    api_router.include_router(inventory_warehouses_router)
    api_router.include_router(inventory_locations_router)
    api_router.include_router(plans_router)
    api_router.include_router(subscriptions_router)
    api_router.include_router(tenants_router, prefix="/platform")
    api_router.include_router(legal_router)
    return api_router
