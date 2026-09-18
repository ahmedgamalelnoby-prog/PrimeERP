from fastapi import APIRouter, Depends
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
from app.modules.platform.api.router import router as platform_modules_router
from app.modules.platform.entitlements.router import router as entitlements_router
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
from app.modules.shipping.accounting_router import router as shipping_accounting_router
from app.modules.shipping.pricing_router import router as shipping_pricing_router
from app.modules.integrations.router import public_router as integrations_public_router
from app.modules.integrations.router import router as integrations_router
from app.modules.integrations.product_mapping_router import router as integration_product_mapping_router
from app.modules.integrations.provider_catalog_router import router as integration_providers_router
from app.modules.uom.router import router as uom_router
from app.modules.companies.router import router as companies_router
from app.modules.branches.router import router as branches_router
from app.modules.treasury.router import router as treasury_router
from app.modules.egyptian_einvoice.router import router as egyptian_einvoice_router
from app.modules.audit.router import router as audit_router
from app.modules.roles.router import router as roles_router
from app.modules.taxes.router import router as taxes_router
from app.modules.catalog.router import router as catalog_router
from app.modules.catalog.variant_router import router as catalog_variant_router
from app.modules.catalog.bundle_router import router as catalog_bundle_router
from app.modules.catalog.pricing_engine_router import router as pricing_engine_router
from app.modules.commissions.router import router as commissions_router
from app.modules.saas.entitlements import require_module
from app.modules.jurisdiction.router import router as jurisdiction_router
from app.modules.reports.router import router as reports_router
from app.modules.helpdesk_ai.router import router as helpdesk_router

def build_router() -> APIRouter:
    api_router = APIRouter()
    api_router.include_router(identity_router, prefix="/identity", tags=["identity"])
    api_router.include_router(features_router)
    api_router.include_router(helpdesk_router)
    api_router.include_router(platform_modules_router)
    api_router.include_router(saas_router, prefix="/saas", tags=["saas"])
    api_router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
    api_router.include_router(fiscal_years_router, prefix="/accounting/fiscal-years", tags=["accounting-fiscal-years"], dependencies=[Depends(require_module("accounting"))])
    api_router.include_router(journal_entries_router, dependencies=[Depends(require_module("accounting"))])
    api_router.include_router(financial_reports_router, dependencies=[Depends(require_module("accounting"))])
    api_router.include_router(accounting_router, dependencies=[Depends(require_module("accounting"))])
    api_router.include_router(taxes_router)
    api_router.include_router(jurisdiction_router)
    for r in (inventory_items_router, inventory_warehouses_router, inventory_locations_router, inventory_stock_moves_router, inventory_transfers_router, inventory_adjustments_router, inventory_reservations_router, inventory_costing_router):
        api_router.include_router(r, dependencies=[Depends(require_module("inventory"))])
    api_router.include_router(catalog_router, dependencies=[Depends(require_module("inventory"))])
    api_router.include_router(catalog_variant_router, dependencies=[Depends(require_module("inventory"))])
    api_router.include_router(catalog_bundle_router, dependencies=[Depends(require_module("inventory"))])
    api_router.include_router(pricing_engine_router, dependencies=[Depends(require_module("inventory"))])
    api_router.include_router(commerce_router, dependencies=[Depends(require_module("sales"))])
    api_router.include_router(enterprise_router, dependencies=[Depends(require_module("enterprise"))])
    api_router.include_router(commissions_router, dependencies=[Depends(require_module("enterprise"))])
    api_router.include_router(shipping_router)
    api_router.include_router(shipping_settlement_router)
    api_router.include_router(shipping_accounting_router)
    api_router.include_router(shipping_pricing_router)
    api_router.include_router(integrations_router)
    api_router.include_router(integration_product_mapping_router)
    api_router.include_router(integration_providers_router)
    api_router.include_router(uom_router)
    api_router.include_router(companies_router)
    api_router.include_router(branches_router)
    api_router.include_router(treasury_router)
    api_router.include_router(egyptian_einvoice_router, dependencies=[Depends(require_module("einvoice"))])
    api_router.include_router(reports_router)
    api_router.include_router(audit_router)
    api_router.include_router(integrations_public_router)
    api_router.include_router(plans_router)
    api_router.include_router(subscriptions_router)
    api_router.include_router(tenants_router, prefix="/platform")
    api_router.include_router(entitlements_router)
    api_router.include_router(roles_router)
    api_router.include_router(legal_router)
    return api_router
