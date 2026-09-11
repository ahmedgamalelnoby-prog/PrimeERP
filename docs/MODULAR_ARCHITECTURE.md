# PrimeERP Modular Architecture

PrimeERP is a **modular monolith + add-on platform**. Domain folders group related capabilities, while each meaningful business capability is an independent installable add-on.

## Non-negotiable rules

1. One add-on = one coherent business responsibility, not one screen/button.
2. Every installable add-on owns its `__manifest__.py` and declares dependencies.
3. Backend add-ons keep models, schemas, services, API, security, data, migrations and tests together.
4. Frontend surfaces mirror the same technical module boundaries.
5. Cross-module integration uses declared contracts/events; modules must not import another module's ORM internals.
6. Platform installation/enabling and tenant entitlement are separate states.
7. User roles/permissions are separate from tenant subscription entitlement.
8. Financial records are reversed/adjusted, never deleted by module lifecycle operations.
9. Legacy root packages are temporary compatibility adapters only.
10. Empty scaffolding is removed when no compatibility import requires it.
11. Industry modules compose common capabilities; they do not duplicate accounting, inventory, identity or security engines.
12. Modular monolith now; extraction to services later is possible because boundaries are explicit.

## Layering

```text
CORE
  ↓
ORGANIZATION / PLATFORM / CONFIGURATION
  ↓
FINANCE / ACCOUNTING
  ↓
BUSINESS: CRM / SALES / INVENTORY / PROJECTS / CONTRACTS
  ↓
PEOPLE
  ↓
INDUSTRY
  ↓
LOCALIZATION / EXTERNAL INTEGRATIONS
```

Lower layers never depend on industry implementations.

## Canonical backend layout

```text
backend/app/modules/<domain>/<addon>/
├── __init__.py
├── __manifest__.py
├── models/
├── schemas/
├── services/
├── api/
├── security/
├── data/
├── migrations/
└── tests/
```

The repository currently contains legacy flat modules. They are retained only where existing imports/API compatibility requires them and are migrated slice-by-slice.

## Canonical finance graph

```text
accounting/accounting_core
├── chart_of_accounts
├── fiscal_periods
├── taxes
├── journal_entries
│   └── journal_items
├── receivables
├── payables
├── bank_reconciliation
├── assets
├── budgets
├── cost_centers
└── reports
```

## Canonical business graph

```text
organization/companies
└── organization/branches

crm/crm_core
├── crm/leads
├── crm/opportunities
└── crm/activities

sales/sales_core
├── sales/quotations
├── sales/sales_orders
├── sales/pricing
├── sales/discounts
├── sales/returns
└── sales/commissions

inventory/inventory_core
├── inventory/products
├── inventory/warehouses
├── inventory/locations
├── inventory/stock_moves
├── inventory/transfers
├── inventory/adjustments
├── inventory/lots
├── inventory/serial_numbers
├── inventory/costing
└── inventory/valuation
```

## End-to-end transaction flow

```text
CRM / Customer
      ↓
Quotation → Sales Order → Delivery / Stock Move
      ↓                    ↓
Invoice / Receivable ← Inventory Valuation
      ↓
Journal Entry → Journal Items
      ↓
Treasury / Bank Reconciliation
      ↓
Reports / Tax / E-Invoice
```

Payroll, assets, purchasing, POS, hospitality, real estate and manufacturing feed the same accounting contracts instead of creating parallel ledgers.

## Industry composition

- **Restaurant:** restaurant core → POS, tables, floors, kitchen, recipes, delivery, loyalty.
- **Hospitality:** hospitality core → rooms, reservations, folios, housekeeping, operator/revenue-share integrations.
- **Real Estate:** real-estate core → properties, units, leases, tenants, rent, revenue share and collections.
- **Retail:** retail core → POS, products, pricing, promotions, stock, returns and loyalty.
- **Manufacturing:** manufacturing core → BOM, work orders, MRP, production, quality and costing.

## SaaS entitlement boundary

```text
Platform Module Catalog
        ↓
Plan / Subscription
        ↓
Tenant Entitlement
        ↓
Module Available to Tenant
        ↓
User Role / Permission
        ↓
Object Access + Business Rules
```

Granting a tenant access must never globally enable a module.

## Migration completion criteria

A module is considered migrated only when:

- its real business logic is inside the canonical add-on;
- its manifest and dependencies are declared;
- existing APIs/database mappings remain compatible or are explicitly versioned;
- tests cover the migrated behavior;
- no module imports another module's internal implementation without a declared boundary;
- legacy compatibility code is no longer required and is deleted.

The migration order is foundation → accounting → sales/purchasing/inventory → people → industry → integrations. This keeps financial and master-data contracts stable while higher-level modules are rebuilt around them.
