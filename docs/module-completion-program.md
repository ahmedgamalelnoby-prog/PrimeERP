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
| Manufacturing / MRP | 🟢 COMPLETE | Production/WIP/FG, BOM/recipe, scrap/by-product, subcontracting, variance and accounting closure. |
| POS / Restaurant | 🟢 COMPLETE | POS → recipe → outlet stock → consumption → payment → COGS, KDS, modifiers/promotions, refunds/voids, outlet profitability. |
| Shipping | 🟢 COMPLETE | Shipment lifecycle, terminal delivered state, returns, carrier pricing, COD settlement/reconciliation, GL. |
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

## Latest completion checkpoint — 2026-09-20

### Accounting — 🟡 IN PROGRESS
- Fiscal year close now validates branch, journal, retained-earnings account, and prevents a second completed close run.
- Year-end tax gate now uses the canonical `TaxReturnDraft` workflow; missing/unreconciled tax returns no longer silently pass the close checklist.
- Financial summary no longer classifies every credit-normal P&L account as revenue; explicit account categories are honored and unsupported categories fail loudly.
- Remaining closure blockers: complete Tax/E-Invoice integration and Accounting frontend parity, then perform the final Accounting review.

### Commerce / Sales / Purchasing — 🟡 IN PROGRESS
- Sales and purchase returns now have stock-backed allocation controls and accounting integration.
- Payment idempotency/reversal and AR/AP allocation controls are in place.
- Remaining closure blockers: final end-to-end UI parity and reconciliation of every document/payment/return path before marking CLOSED.

### Inventory / WMS — 🟢 COMPLETE (functional closure; Release Gate pending)
- WMS tenant/company/warehouse/location/reservation controls are hardened.
- FIFO valuation now isolates cost layers by variant where the layer schema supports variants.
- Inventory accounting configuration now enforces tenant + company account ownership.
- Functional closure completed: warehouses/locations, reservations, stock moves, transfers, WMS, negative-stock controls, FIFO/weighted/standard costing, valuation reconciliation, reversals, accounting posting, tenant/company isolation, audit trail, and frontend operational routes are connected. Final Release Gate remains the only verification layer.

### Process rule
The next work should continue with the active module's closure checklist. A module is not marked CLOSED because one endpoint works; it is closed only after its full workflow and integrations pass the documented completion definition. Closed modules are not reopened for unrelated enhancements.

## First completion pass
Treasury received a broad integration hardening pass:
- fixed treasury runtime use of Decimal in positions;
- fixed TreasuryTransaction → JournalEntry source_id type;
- fixed cheque GL source_id type;
- made cheque GL idempotency unique per cheque event without violating the integer source-id contract.

No release tests are being run in this functional-completion phase. The final Release Gate remains a separate phase after all modules are closed.
### Manufacturing / MRP — 🟢 COMPLETE (functional closure; Release Gate pending)
- Production order/work-order lifecycle, recipe explosion, variant-aware ingredients, reservations, material consumption, finished-goods receipt and partial production are connected.
- Labor, overhead, subcontracting, scrap/by-product, production costing, variance posting and WIP settlement are integrated with Accounting/Inventory.
- Work-order finalization and output idempotency are hardened.
- MRP requirements, shortage-driven production, work centers, routings, scheduling conflicts and production-cost records are connected.
- Tenant/company isolation and transition controls are enforced. Final Release Gate remains pending.
### POS / Restaurant — 🟢 COMPLETE (functional closure; Release Gate pending)
- Outlet/branch/warehouse, terminals, menus/prices, stations/KDS routing, recipes, outlet consumption, modifiers, promotions, checkout, payments, refunds and voids are connected.
- Restaurant flow supports outlet warehouse consumption and preparation routing. Final Release Gate remains pending.
### Shipping — 🟢 COMPLETE (functional closure; Release Gate pending)
- Carrier/method master data, pricing rules, shipment lifecycle, terminal delivered state, returns, COD, carrier fees, withdrawal/card fees, settlement, reconciliation and GL events are connected.
- Shipment/company/tenant/account/journal/branch controls are enforced. Final Release Gate remains pending.

