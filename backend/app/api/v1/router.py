from fastapi import APIRouter
from app.modules.accounting.fiscal_years.api.router import router as fiscal_years_router
from app.modules.accounting.journals.api.journal_entries import router as journal_entries_router
from app.modules.accounting.reports.router import router as financial_reports_router
from app.modules.accounting.router import router as accounting_router
from app.modules.identity.api.router import router as identity_router
from app.modules.inventory.adjustments.router import router as inventory_adjustments_router
from app.modules.inventory.costing.router import router as inventory_costing_router
from app.modules.inventory.items.router import router as inventory_items_router
from app.modules.inventory.locations.router import router as inventory_locations_router
from app.modules.inventory.reservations.router import router as inventory_reservations_router
from app.modules.inventory.stock_moves.router import router as inventory_stock_moves_router
from app.modules.inventory.transfers.router import router as inventory_transfers_router
from app.modules.inventory.warehouses.router import router as inventory_warehouses_router
from app.modules.legal.router import router as legal_router
from app.modules.platform.features.router import router as features_router
from app.modules.platform.plans.router import router as plans_router
from app.modules.platform.subscriptions.router import router as subscriptions_router
from app.modules.platform.tenants.router import router as tenants_router
from app.modules.saas.router import router as saas_router
from app.modules.transactions.api.router import router as transactions_router
from app.modules.commerce.router import router as commerce_router
from app.modules.enterprise.router import router as enterprise_router
from app.modules.shipping.router import router as shipping_router
from app.modules.shipping.settlement_router import router as shipping_settlement_router
from app.modules.integrations.router import router as integrations_router
from app.modules.uom.router import router as uom_router


def build_router() -> APIRouter:
    api_router = APIRouter()
    api_router.include_router(identity_router, prefix="/identity", tags=["identity"])
    api_router.include_router(features_router)
    api_router.include_router(saas_router, prefix="/saas", tags=["saas"])
    api_router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
    api_router.include_router(fiscal_years_router, prefix="/accounting/fiscal-years", tags=["accounting-fiscal-years"])
    api_router.include_router(journal_entries_router)
    api_router.include_router(financial_reports_router)
    api_router.include_router(accounting_router)
    for r in (
        inventory_items_router,
        inventory_warehouses_router,
        inventory_locations_router,
        inventory_stock_moves_router,
        inventory_transfers_router,
        inventory_adjustments_router,
        inventory_reservations_router,
        inventory_costing_router,
        commerce_router,
        enterprise_router,
        shipping_router,
        shipping_settlement_router,
        integrations_router,
        uom_router,
    ):
        api_router.include_router(r)
    api_router.include_router(plans_router)
    api_router.include_router(subscriptions_router)
    api_router.include_router(tenants_router, prefix="/platform")
    api_router.include_router(legal_router)
    return api_router
