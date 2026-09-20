# PrimeERP Module Completion Program

This registry is the single source of truth for functional completion. A module is CLOSED only after its defined workflow, integrations, controls, accounting/stock effects, reversals/returns, period locks, tenant isolation, audit, reports, API and frontend parity are reviewed.

## Status
- 🟢 COMPLETE: no known functional gap in the defined scope.
- 🟡 IN PROGRESS: active completion work; explicit gaps are listed.
- 🔴 BLOCKED: completion depends on a named module/dependency.
- A closed module is not reopened for unrelated work. It is revisited only for a documented dependency/blocker.

## Completion order
1. Accounting
2. Commerce / Sales / Purchasing
3. Inventory / WMS
4. Treasury / Cheques
5. Manufacturing / MRP
6. POS / Restaurant
7. Shipping
8. Catalog / Products / Recipes
9. CRM / Sales
10. HR / Organization
11. Tax / Egyptian E-Invoice
12. SaaS / Companies / Tenants
13. Reports / BI / AI
14. Integrations
15. Security / Audit / Approvals
16. Frontend parity
17. Release Gate

## Current board

| Module | Status | Closure blockers / scope |
|---|---|---|
| Accounting | 🟡 IN PROGRESS | Complete GL lifecycle, period lock, dimensions, reversals, subledger integration, reporting, tenant isolation, frontend parity. |
| Commerce / Sales / Purchasing | 🟡 IN PROGRESS | Sales/purchase lifecycle, AR/AP, payments, returns, allocations, accounting and inventory integration. |
| Inventory / WMS | 🟡 IN PROGRESS | Reservations, picking, transfers, costing, negative stock policy, warehouse/location isolation, accounting integration. |
| Treasury / Cheques | 🟡 IN PROGRESS | Treasury transaction lifecycle, cheque lifecycle + GL, bank reconciliation, daily closing, forecasts, all-account reconciliation, tenant isolation, reports/UI. |
| Manufacturing / MRP | 🟡 IN PROGRESS | Production/WIP/FG, BOM/recipe, scrap/by-product, subcontracting, variance and accounting closure. |
| POS / Restaurant | 🟡 IN PROGRESS | POS → recipe → outlet stock → consumption → payment → COGS, KDS, modifiers/promotions, refunds/voids, outlet profitability. |
| Shipping | 🟡 IN PROGRESS | Shipment lifecycle, terminal delivered state, returns, carrier pricing, COD settlement/reconciliation, GL. |
| Catalog / Products / Recipes | 🟡 IN PROGRESS | SKU/variant lifecycle, recipes, external SKU mappings and downstream integrations. |
| CRM / Sales | 🟡 IN PROGRESS | Lead → opportunity → quotation → customer/order integration and accounting/fulfillment links. |
| HR / Organization | 🟡 IN PROGRESS | Employees/departments/users, organization scope and approval/permission integration. |
| Tax / Egyptian E-Invoice | 🟡 IN PROGRESS | Tax engine, VAT/WHT, returns, e-invoice/credit/debit notes and accounting integration. |
| SaaS / Companies / Tenants | 🟡 IN PROGRESS | Plans, entitlements, expiry locks, company/branch/warehouse/user limits and isolation. |
| Reports / BI / AI | 🟡 IN PROGRESS | Financial/operational reports, dashboards, AI analysis and scheduled delivery. |
| Integrations | 🟡 IN PROGRESS | Salla and other commerce/shipping integrations, webhooks and end-to-end orchestration. |
| Security / Audit / Approvals | 🟡 IN PROGRESS | RBAC, record-level isolation, API-key security, sessions, approvals, audit and controls. |
| Frontend parity | 🟡 IN PROGRESS | Every production API/workflow exposed through coherent UI and error/state handling. |
| Release Gate | 🔴 BLOCKED | Starts only after all functional modules are CLOSED. |

## First completion pass
Treasury received a broad integration hardening pass:
- fixed treasury runtime use of Decimal in positions;
- fixed TreasuryTransaction → JournalEntry source_id type;
- fixed cheque GL source_id type;
- made cheque GL idempotency unique per cheque event without violating the integer source-id contract.

No release tests are being run in this functional-completion phase. The final Release Gate remains a separate phase after all modules are closed.
