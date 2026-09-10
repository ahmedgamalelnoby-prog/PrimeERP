# PrimeERP Modular Architecture

PrimeERP uses a **modular monolith + add-on engine**. Domain folders group related capabilities, while each meaningful business capability is an independent add-on.

## Rules

1. A module has one coherent business responsibility; do not create an add-on for a single button or UI action.
2. Every add-on owns its backend models, schemas, services, API, permissions, data, migrations, tests, and frontend surface where applicable.
3. Every add-on declares dependencies in `__manifest__.py`.
4. Cross-module imports must follow declared dependencies. Optional integrations use contracts/events rather than hard imports.
5. The core module engine owns discovery, dependency validation, installation state, activation state, and the future SaaS entitlement boundary.
6. Existing modules are migrated incrementally. Compatibility adapters keep existing APIs working during migration.
7. Do not convert PrimeERP into microservices at this stage. The modular boundaries are designed so a high-value module can be extracted later if scale requires it.

## Backend layout

```text
backend/app/
├── core/
│   └── module_engine/
└── modules/
    ├── accounting/
    │   ├── accounting_core/
    │   ├── chart_of_accounts/
    │   ├── journal_entries/
    │   ├── taxes/
    │   ├── receivables/
    │   └── ...
    ├── sales/
    │   ├── sales_core/
    │   ├── quotations/
    │   ├── sales_orders/
    │   ├── pricing/
    │   └── ...
    └── inventory/
        ├── inventory_core/
        ├── products/
        ├── warehouses/
        ├── stock_moves/
        └── ...
```

Each add-on follows:

```text
<addon>/
├── __init__.py
├── __manifest__.py
├── models/
├── schemas/
├── services/
├── api/
├── security/
├── data/
├── migrations/
├── tests/
└── frontend/
```

## Dependency example

```text
sales/sales_core
    ├── sales/quotations
    ├── sales/sales_orders
    ├── sales/sales_inventory
    ├── sales/sales_accounting
    └── sales/sales_delivery
```

The registry validates missing dependencies and circular dependency graphs before activation.

## SaaS boundary

Module availability is separate from user permissions:

```text
Platform catalog
      ↓
Customer plan / entitlement
      ↓
Tenant module enabled
      ↓
User permission
      ↓
Business rule / object access
```

This allows PrimeERP to sell individual modules, bundles, users, branches, and future add-ons without coupling billing logic to business modules.

## Migration strategy

The current PrimeERP modules are not blindly moved in one commit. Existing functionality remains intact while capabilities are extracted into add-ons one domain at a time. Compatibility routers/adapters are retained until consumers are migrated, then removed.
