"""Canonical identity bridge between technical modules and SaaS entitlements.

The module engine uses granular technical names while the SaaS database/API uses
business-level module codes. This file is the single translation boundary.
"""

from __future__ import annotations

from typing import Final

# Business entitlement code -> technical modules covered by that entitlement.
BUSINESS_TO_TECHNICAL: Final[dict[str, tuple[str, ...]]] = {
    "dashboard": ("core/identity",),
    "users": ("core/identity", "core/security"),
    "companies": ("organization/companies",),
    "branches": ("organization/branches",),
    "accounting": (
        "accounting/accounting_core",
        "accounting/chart_of_accounts",
        "accounting/journal_entries",
        "accounting/journal_items",
        "accounting/fiscal_periods",
        "accounting/taxes",
        "accounting/vat",
        "accounting/withholding_tax",
        "accounting/receivables",
        "accounting/payables",
        "accounting/bank_reconciliation",
        "accounting/assets",
        "accounting/budgets",
        "accounting/cost_centers",
        "accounting/reports",
    ),
    "taxes": (
        "accounting/taxes",
        "accounting/vat",
        "accounting/withholding_tax",
    ),
    "sales": (
        "sales/sales_core",
        "sales/quotations",
        "sales/sales_orders",
        "sales/pricing",
        "sales/discounts",
        "sales/returns",
        "sales/commissions",
    ),
    "inventory": (
        "inventory/inventory_core",
        "inventory/warehouses",
        "inventory/locations",
        "inventory/stock_moves",
        "inventory/reservations",
        "inventory/transfers",
        "inventory/adjustments",
        "inventory/lots",
        "inventory/serial_numbers",
        "inventory/costing",
        "inventory/valuation",
    ),
    # Purchasing is implemented as the commerce sales/purchasing boundary;
    # entitlement identity must therefore point at the real technical add-on.
    "purchasing": ("commerce/sales_purchasing",),
    "shipping": ("logistics/shipping",),
    "integrations": ("integrations/core",),
    "treasury": ("treasury/core",),
    "crm": ("crm/crm_core", "crm/leads", "crm/opportunities", "crm/activities"),
    "hr": ("people/hr_core", "people/employees", "people/attendance", "people/payroll"),
    "restaurant": ("industry/restaurant_core", "industry/restaurant_pos"),
    "hospitality": ("industry/hospitality_core",),
    "real_estate": ("industry/real_estate_core",),
    "retail": ("industry/retail_core",),
    "manufacturing": ("industry/manufacturing_core",),
    "einvoice": ("localization/egyptian_einvoice",),
}

TECHNICAL_TO_BUSINESS: Final[dict[str, str]] = {
    technical: business
    for business, technical_modules in BUSINESS_TO_TECHNICAL.items()
    for technical in technical_modules
}

# Backward-compatible aliases used by older migrations and API routes.
# Every alias must resolve to a release-level entitlement, never to an
# implementation-only submodule.
ALIASES: Final[dict[str, str]] = {
    "egyptian_einvoice": "einvoice",
    "einvoice": "einvoice",
    "tax": "taxes",
    "fixed_assets": "accounting",
    "purchase": "purchasing",
    "purchases": "purchasing",
}


def canonical_business_code(code: str) -> str:
    normalized = code.strip().lower()
    return ALIASES.get(normalized, normalized)


def technical_modules_for(code: str) -> tuple[str, ...]:
    canonical = canonical_business_code(code)
    return BUSINESS_TO_TECHNICAL.get(canonical, ())


def business_code_for_technical(technical_name: str) -> str | None:
    return TECHNICAL_TO_BUSINESS.get(technical_name)
