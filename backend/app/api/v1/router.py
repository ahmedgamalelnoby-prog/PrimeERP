from fastapi import APIRouter
from app.modules.identity.api.router import router as identity_router
from app.modules.saas.router import router as saas_router
from app.modules.transactions.api.router import router as transactions_router
from app.modules.accounting.fiscal_years.api.router import router as fiscal_years_router
from app.modules.accounting.journals.api.router import router as journals_router
from app.modules.accounting.chart_of_accounts.router import router as chart_of_accounts_router
from app.modules.platform.features.router import router as features_router
from app.modules.platform.plans.router import router as plans_router
from app.modules.platform.tenants.router import router as tenants_router
from app.modules.legal.router import router as legal_router
from app.modules.companies.router import router as companies_router
from app.modules.branches.router import router as branches_router
from app.modules.customers.router import router as customers_router
from app.modules.products.router import router as products_router
from app.modules.inventory.router import router as inventory_router
from app.modules.sales.sales_orders.router import router as sales_orders_router
def build_router()->APIRouter:
    api_router=APIRouter()
    api_router.include_router(identity_router,prefix="/identity",tags=["identity"])
    api_router.include_router(features_router)
    api_router.include_router(saas_router,prefix="/saas",tags=["saas"])
    api_router.include_router(transactions_router,prefix="/transactions",tags=["transactions"])
    api_router.include_router(fiscal_years_router,prefix="/accounting/fiscal-years",tags=["accounting-fiscal-years"])
    api_router.include_router(chart_of_accounts_router,prefix="/accounting/chart",tags=["accounting-chart"])
    api_router.include_router(journals_router,prefix="/accounting",tags=["accounting-journals"])
    api_router.include_router(plans_router)
    api_router.include_router(tenants_router,prefix="/platform")
    api_router.include_router(companies_router)
    api_router.include_router(branches_router)
    api_router.include_router(customers_router)
    api_router.include_router(products_router)
    api_router.include_router(inventory_router)
    api_router.include_router(sales_orders_router,prefix="/sales",tags=["sales-orders"])
    api_router.include_router(legal_router)
    return api_router
