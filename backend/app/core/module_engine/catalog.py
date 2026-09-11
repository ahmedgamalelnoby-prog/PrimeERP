"""Canonical PrimeERP add-on catalog and dependency policy."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True, slots=True)
class CatalogEntry:
    technical_name: str
    domain: str
    dependencies: Tuple[str, ...] = ()
    layer: str = "business"

CORE = (
    CatalogEntry("core/identity", "core", layer="core"), CatalogEntry("core/security", "core", ("core/identity",), layer="core"),
    CatalogEntry("core/audit", "core", ("core/identity",), layer="core"), CatalogEntry("core/workflow", "core", ("core/identity",), layer="core"),
    CatalogEntry("core/notifications", "core", ("core/identity",), layer="core"),
)
ORGANIZATION = (CatalogEntry("organization/companies", "organization", ("core/identity",), layer="foundation"), CatalogEntry("organization/branches", "organization", ("organization/companies",), layer="foundation"))
ACCOUNTING = (
    CatalogEntry("accounting/accounting_core", "accounting", ("organization/companies",), layer="finance"), CatalogEntry("accounting/chart_of_accounts", "accounting", ("accounting/accounting_core",), layer="finance"),
    CatalogEntry("accounting/journal_entries", "accounting", ("accounting/accounting_core", "accounting/chart_of_accounts"), layer="finance"), CatalogEntry("accounting/journal_items", "accounting", ("accounting/journal_entries",), layer="finance"),
    CatalogEntry("accounting/fiscal_periods", "accounting", ("accounting/accounting_core",), layer="finance"), CatalogEntry("accounting/taxes", "accounting", ("accounting/accounting_core",), layer="finance"),
    CatalogEntry("accounting/vat", "accounting", ("accounting/taxes",), layer="finance"), CatalogEntry("accounting/withholding_tax", "accounting", ("accounting/taxes",), layer="finance"),
    CatalogEntry("accounting/receivables", "accounting", ("accounting/journal_entries",), layer="finance"), CatalogEntry("accounting/payables", "accounting", ("accounting/journal_entries",), layer="finance"),
    CatalogEntry("accounting/bank_reconciliation", "accounting", ("accounting/journal_entries", "treasury/core"), layer="finance"), CatalogEntry("accounting/assets", "accounting", ("accounting/journal_entries",), layer="finance"),
    CatalogEntry("accounting/budgets", "accounting", ("accounting/accounting_core",), layer="finance"), CatalogEntry("accounting/cost_centers", "accounting", ("accounting/accounting_core",), layer="finance"),
    CatalogEntry("accounting/reports", "accounting", ("accounting/journal_entries",), layer="finance"),
)
TREASURY = (CatalogEntry("treasury/core", "treasury", ("accounting/journal_entries", "platform/customers"), layer="finance"),)
SALES = (
    CatalogEntry("sales/sales_core", "sales", ("organization/companies", "platform/customers", "inventory/warehouses"), layer="business"), CatalogEntry("sales/quotations", "sales", ("sales/sales_core",), layer="business"), CatalogEntry("sales/sales_orders", "sales", ("sales/sales_core",), layer="business"),
    CatalogEntry("sales/pricing", "sales", ("sales/sales_core",), layer="business"), CatalogEntry("sales/discounts", "sales", ("sales/pricing",), layer="business"), CatalogEntry("sales/returns", "sales", ("sales/sales_orders",), layer="business"), CatalogEntry("sales/commissions", "sales", ("sales/sales_orders",), layer="business"),
)
INVENTORY = (
    CatalogEntry("inventory/inventory_core", "inventory", ("organization/companies",), layer="business"), CatalogEntry("inventory/warehouses", "inventory", ("inventory/inventory_core",), layer="business"), CatalogEntry("inventory/locations", "inventory", ("inventory/warehouses",), layer="business"), CatalogEntry("inventory/stock_moves", "inventory", ("inventory/inventory_core", "inventory/locations"), layer="business"),
    CatalogEntry("inventory/reservations", "inventory", ("inventory/stock_moves",), layer="business"), CatalogEntry("inventory/transfers", "inventory", ("inventory/stock_moves", "inventory/reservations"), layer="business"), CatalogEntry("inventory/adjustments", "inventory", ("inventory/stock_moves",), layer="business"), CatalogEntry("inventory/lots", "inventory", ("inventory/inventory_core",), layer="business"), CatalogEntry("inventory/serial_numbers", "inventory", ("inventory/inventory_core",), layer="business"), CatalogEntry("inventory/costing", "inventory", ("inventory/stock_moves",), layer="finance"), CatalogEntry("inventory/valuation", "inventory", ("inventory/costing", "accounting/journal_entries"), layer="finance"),
)
PURCHASING = (CatalogEntry("purchasing/suppliers", "purchasing", ("organization/companies",), layer="business"), CatalogEntry("purchasing/purchase_orders", "purchasing", ("purchasing/suppliers", "inventory/inventory_core", "inventory/warehouses"), layer="business"))
PLATFORM = (CatalogEntry("platform/customers", "platform", ("core/identity", "organization/companies"), layer="platform"), CatalogEntry("platform/plans", "platform", (), layer="platform"), CatalogEntry("platform/subscriptions", "platform", ("platform/customers", "platform/plans"), layer="platform"), CatalogEntry("platform/billing", "platform", ("platform/subscriptions",), layer="platform"), CatalogEntry("platform/usage", "platform", ("platform/subscriptions",), layer="platform"))
CRM = (CatalogEntry("crm/crm_core", "crm", ("organization/companies",), layer="business"), CatalogEntry("crm/leads", "crm", ("crm/crm_core",), layer="business"), CatalogEntry("crm/opportunities", "crm", ("crm/leads",), layer="business"), CatalogEntry("crm/activities", "crm", ("crm/crm_core",), layer="business"))
PEOPLE = (CatalogEntry("people/hr_core", "people", ("organization/companies",), layer="people"), CatalogEntry("people/employees", "people", ("people/hr_core",), layer="people"), CatalogEntry("people/attendance", "people", ("people/employees",), layer="people"), CatalogEntry("people/payroll", "people", ("people/employees", "accounting/journal_entries"), layer="people"))
INDUSTRY = (CatalogEntry("industry/restaurant_core", "industry", ("inventory/inventory_core", "sales/sales_core"), layer="industry"), CatalogEntry("industry/restaurant_pos", "industry", ("industry/restaurant_core",), layer="industry"), CatalogEntry("industry/hospitality_core", "industry", ("accounting/accounting_core", "sales/sales_core"), layer="industry"), CatalogEntry("industry/real_estate_core", "industry", ("accounting/accounting_core", "sales/sales_core"), layer="industry"), CatalogEntry("industry/retail_core", "industry", ("inventory/inventory_core", "sales/sales_core"), layer="industry"), CatalogEntry("industry/manufacturing_core", "industry", ("inventory/inventory_core", "accounting/accounting_core"), layer="industry"))
LOCALIZATION = (CatalogEntry("localization/egypt_einvoice", "localization", ("accounting/taxes", "accounting/journal_entries"), layer="localization"),)
ALL_CATALOG_ENTRIES = CORE + ORGANIZATION + ACCOUNTING + TREASURY + SALES + INVENTORY + PURCHASING + PLATFORM + CRM + PEOPLE + INDUSTRY + LOCALIZATION

def catalog() -> Tuple[CatalogEntry, ...]: return ALL_CATALOG_ENTRIES

def catalog_keys() -> set[str]: return {entry.technical_name for entry in ALL_CATALOG_ENTRIES}
