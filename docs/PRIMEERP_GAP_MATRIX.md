# PrimeERP — Global Gap Matrix
Date: 2026-09-21
Branch: feature/modern-ui-legal-admin
Audit baseline commit: 4b70fad5a77f44cbc4cc97c454e9b546811a4996

## Audit objective
Establish one repository-wide completion baseline before implementing more features or running the final Release Gate. Findings are grouped by business cycle and cross-module dependency, not by individual test failures.

## Current repository inventory
- 3,061 tracked tree paths
- 1,917 Python files
- 453 TypeScript/TSX files
- 19 Alembic migration files
- 37 backend module directories detected (excluding the package __init__.py entry)
- 61 frontend page-like files

## Wave 1 — Architecture / dependency baseline
Status: AUDITED
- Central API router includes Identity, SaaS, Transactions, Accounting, Platform, Legal, Companies, Branches, Customers, Products, Inventory, Sales, Purchasing, POS, Treasury and Shipping.
- Central SQLAlchemy model registry currently includes the newer Sales and Shipping models.
- The legacy project analyzer report is stale (dated 2026-07-28) and must not be treated as the current completion metric.
- Repository search on the current GitHub code-search index did not expose the requested placeholder markers; this is only a static signal and does not replace compilation/runtime validation.
- The current frontend contains many shared scaffold files with zero-byte content; these require a build/import audit before being considered reusable infrastructure.

## Wave 2 — Core business-cycle gaps
### Accounting
- Complete operational journal lifecycle across every source module.
- Add/verify AR, AP, receipts, payments, allocations, reversals and source-document traceability.
- Complete inventory valuation and COGS postings.
- Complete period-close/lock enforcement.
- Complete financial reports from posted journals only.
- Complete VAT/WHT/e-invoice integration where applicable.

### Sales
- Existing order -> reservation -> issue -> invoice -> journal foundation exists.
- Remaining: returns/credit notes, customer receipts/allocation, pricing/discount rules, tax/account mapping hardening, full UI workflow and end-to-end source-document traceability.

### Purchasing
- Existing supplier -> PO -> receipt -> inventory -> invoice -> journal foundation exists.
- Remaining: returns/debit notes, AP payment/allocation, price/tax/account controls, approval/period rules, full UI workflow.

### Inventory
- Existing warehouse/location/stock/reservation/issue foundations exist.
- Remaining: valuation method, COGS integration, stock adjustments/counts, transfer lifecycle hardening, negative-stock policy, source-document traceability, outlet consumption and complete UI.

### POS
- Existing outlet/terminal/session/order/payment foundation exists.
- Remaining: menu/pricing integration, kitchen/bar routing, outlet-store consumption, accounting posting, refunds/returns, session close/reconciliation, cashier controls and complete UI.

### Treasury / Cheques
- Existing accounts/transactions/transfers/cheques/allocations foundation exists.
- Remaining: receipt/payment accounting, balances, deposit/withdrawal lifecycle, cheque issue/deposit/clear/bounce/return, reversals, reconciliation and UI.

### Shipping / Marketplaces
- Existing carrier/rule/shipment/return/settlement foundation exists.
- Remaining: actual rule calculation, shipment-to-inventory reservation/issue, Salla/marketplace adapters and mappings, carrier settlement accounting, COD/withdrawal accounting, returns/refunds, money-due reports and UI.

## Wave 3 — Governance / platform
- Approvals must be enforced at transaction boundaries, not only represented as data.
- Period lock must block all posting/stock/treasury mutations consistently.
- Tenant isolation requires repository-wide positive and negative tests, including cross-company/branch references.
- Roles/permissions require endpoint-level enforcement and frontend visibility consistency.
- SaaS subscription/trial/expiry/payment controls require complete lifecycle enforcement.
- Audit trail must capture material financial and inventory mutations with actor/source references.

## Wave 4 — Frontend/API parity
- Replace shallow/static dashboards with live APIs.
- Remove obsolete workflow/list screens and dead routes.
- Ensure every implemented backend business cycle has usable list/create/detail/action UI.
- Replace zero-byte shared components only where imported/needed; otherwise remove dead scaffolding.
- Align DTOs, enums, IDs, validation and error handling between frontend and backend.

## Wave 5 — Migration / data integrity
- Verify the complete Alembic graph has exactly one head.
- Verify fresh PostgreSQL 17 upgrade from empty database.
- Verify downgrade/upgrade safety for newly introduced foundations where supported.
- Verify every new model is imported into the metadata registry.
- Verify FK/index/unique/check constraints and tenant scoping.
- Verify numbering sequences are transaction-safe and cannot create duplicate business numbers.

## Wave 6 — Release Gate
Do not call PrimeERP complete until all preceding waves are implemented and this gate passes:
1. Backend compile/static checks.
2. Full backend tests.
3. Alembic upgrade head + alembic check.
4. Tenant isolation tests.
5. Cross-module end-to-end tests.
6. Frontend lint + build.
7. Docker build/start/health.
8. API/frontend contract verification.
9. Repository hygiene.
10. Final smoke tests for Sales, Purchasing, Inventory, POS, Treasury, Shipping and Accounting.

## Execution order
Architecture baseline -> business-cycle batch implementation -> cross-module integration -> governance hardening -> frontend parity -> migration/data-integrity audit -> one final Release Gate.
