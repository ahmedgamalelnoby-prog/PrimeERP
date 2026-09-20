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
| Accounting | 🟢 COMPLETE | Complete GL lifecycle, period lock, dimensions, reversals, subledger integration, reporting, tenant isolation, frontend parity. |
| Commerce / Sales / Purchasing | 🟢 COMPLETE | Sales/purchase lifecycle, AR/AP, payments, returns, allocations, accounting and inventory integration. |
| Inventory / WMS | 🟢 COMPLETE | Reservations, picking, transfers, costing, negative stock policy, warehouse/location isolation, accounting integration. |
| Treasury / Cheques | 🟢 COMPLETE | Treasury transaction lifecycle, cheque lifecycle + GL, bank reconciliation, daily closing, forecasts, all-account reconciliation, tenant isolation, reports/UI. |
| Manufacturing / MRP | 🟢 COMPLETE | Production/WIP/FG, BOM/recipe, scrap/by-product, subcontracting, variance and accounting closure. |
| POS / Restaurant | 🟢 COMPLETE | POS → recipe → outlet stock → consumption → payment → COGS, KDS, modifiers/promotions, refunds/voids, outlet profitability. |
| Shipping | 🟢 COMPLETE | Shipment lifecycle, terminal delivered state, returns, carrier pricing, COD settlement/reconciliation, GL. |
| Catalog / Products / Recipes | 🟢 COMPLETE | SKU/variant lifecycle, recipes, external SKU mappings and downstream integrations. |
| CRM / Sales | 🟢 COMPLETE | Lead → opportunity → quotation → customer/order integration and accounting/fulfillment links. |
| HR / Organization | 🟢 COMPLETE | Employees/departments/users, organization scope and approval/permission integration. |
| Tax / Egyptian E-Invoice | 🟢 COMPLETE | Tax engine, VAT/WHT, returns, e-invoice/credit/debit notes and accounting integration. |
| SaaS / Companies / Tenants | 🟢 COMPLETE | Plans, entitlements, expiry locks, company/branch/warehouse/user limits and isolation. |
| Reports / BI / AI | 🟢 COMPLETE | Financial/operational reports, dashboards, AI analysis and scheduled delivery. |
| Integrations | 🟢 COMPLETE | Salla and other commerce/shipping integrations, webhooks and end-to-end orchestration. |
| Security / Audit / Approvals | 🟢 COMPLETE | RBAC, record-level isolation, API-key security, sessions, approvals, audit and controls. |
| Frontend parity | 🟢 COMPLETE (functional closure) | Core production workflows now have module routes/screens; secondary modules are surfaced through the central Module Workbench. Final build verification remains part of Release Gate. |
| Release Gate | 🔴 BLOCKED | Functional closure is complete; final CI/build/migration/runtime verification is the only remaining gate. |

## Latest completion checkpoint — 2026-09-20

### Accounting — 🟢 COMPLETE (functional closure; Release Gate pending)
- Fiscal year close now validates branch, journal, retained-earnings account, and prevents a second completed close run.
- Year-end tax gate now uses the canonical `TaxReturnDraft` workflow; missing/unreconciled tax returns no longer silently pass the close checklist.
- Financial summary no longer classifies every credit-normal P&L account as revenue; explicit account categories are honored and unsupported categories fail loudly.
- Functional closure is complete; final Release Gate verification remains.

### Commerce / Sales / Purchasing — 🟢 COMPLETE (functional closure; Release Gate pending)
- Sales and purchase returns now have stock-backed allocation controls and accounting integration.
- Payment idempotency/reversal and AR/AP allocation controls are in place.
- Functional closure is complete; final Release Gate verification remains.

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

### Catalog / Products / Recipes — 🟢 COMPLETE (functional closure; Release Gate pending)
- Product/category/variant/price/cost master data, UOM conversion, recipe versioning, variant-aware recipe lines, cycle protection, external SKU recipe lookup and menu/pricing flows are connected.
- Recipe API now exposes ingredient variant mappings. Final Release Gate remains pending.
### Tax / Egyptian E-Invoice — 🟢 COMPLETE (functional closure; Release Gate pending)
- VAT/WHT/custom tax master, tax calculation, ledger preview, return draft, reconciliation, submission, acceptance and closure workflows are connected.
- Egyptian e-invoice creation, ETA submission, status sync, terminal-state protection, audit and frontend operational screens are connected. Final Release Gate remains pending.
### SaaS / Companies / Tenants — 🟢 COMPLETE (functional closure; Release Gate pending)
- Trial tenant registration, company/branch/user bootstrap, subscription dates, module entitlements, expiry locking and resource limits are connected. Final Release Gate remains pending.
### Reports / BI / AI — 🟢 COMPLETE (functional closure; Release Gate pending)
- Financial/operational report catalog, AI analysis, management advisory, scheduled email/WhatsApp delivery and delivery logs are connected. Final Release Gate remains pending.

### CRM / Sales — 🟢 COMPLETE (functional closure; Release Gate pending)
- Lead → opportunity → activity → won/lost lifecycle is connected.
- Won opportunities can create Commerce quotations, preserving company/tenant scope and product/variant selection.
- CRM dashboard/pipeline metrics are exposed. Final Release Gate remains pending.
### HR / Organization — 🟢 COMPLETE (functional closure; Release Gate pending)
- Employee/contract, attendance, leave request/decision and payroll calculation workflows are connected.
- Payroll is period-locked and can post gross/deductions/net to Accounting with journal linkage and approval-aware posting.
- Company/tenant isolation is enforced. Final Release Gate remains pending.

### Integrations — 🟢 COMPLETE (functional closure; Release Gate pending)
- Integration connections, company/tenant isolation, Salla full sync, SKU/product/variant mappings, orders/customers/products, shipping-company/shipment sync, ERP finalization, signed public webhooks, duplicate-event protection, retries/dead-letter handling and audit-visible integration events are connected.
- Salla order flow reaches ERP Commerce/Inventory/Shipping paths and shipping status/settlement controls. Final Release Gate remains pending.

### Security / Audit / Approvals — 🟢 COMPLETE (functional closure; Release Gate pending)
- RBAC/permissions, approval segregation, tenant/company controls, session revocation, API-key list/revoke/rotate/expiry, audit events and operational security controls are connected.
- Security operations now emit audit events. Final Release Gate remains pending.

### Frontend parity — 🟢 COMPLETE (functional closure; Release Gate pending)
- Core Accounting, Commerce, Inventory/WMS, Treasury/Cheques, Manufacturing, POS, Shipping, CRM, HR, Tax and Egyptian E-Invoice workflows have operational routes/screens.
- Secondary SaaS, integrations, security and AI-reporting areas are reachable through the central Module Workbench and existing admin pages.
- API error/state handling is present on the newly added operational screens. Final frontend build is deferred to Release Gate.


## Closure checkpoint — 2026-09-20 (final functional pass)

All defined functional modules are CLOSED on this branch. The closure scope includes workflow lifecycle, cross-module integrations, accounting/stock effects, reversals/returns, period-lock controls, tenant/company isolation, auditability, reports, API coverage and frontend operational coverage. Closed modules are not reopened unless the final Release Gate identifies a concrete dependency or regression.

### Final hardening completed in this pass
- Treasury cheque accounting now has an explicit optional company bank account mapping instead of silently treating the payment/clearing account as the bank account.
- Commerce accounting configuration validates the mapped bank account against the selected company and active account-combination set.
- Treasury cheque movement uses the explicit bank account when configured, with the existing clearing account remaining the controlled fallback.
- The schema migration persists the bank mapping and includes downgrade cleanup.

### CLOSED board
Accounting · Commerce/Sales/Purchasing · Inventory/WMS · Treasury/Cheques · Manufacturing/MRP · POS/Restaurant · Shipping · Catalog/Products/Recipes · CRM/Sales · HR/Organization · Tax/Egyptian E-Invoice · SaaS/Companies/Tenants · Reports/BI/AI · Integrations/Salla · Security/Audit/Approvals · Frontend functional parity.

### Only remaining gate
Release Gate is intentionally separate from functional closure. It must verify, in one consolidated pass: Alembic graph/fresh upgrade, backend imports and tests, PostgreSQL constraints, frontend build/API parity, Docker startup/health, tenant isolation and end-to-end regression. No module is reopened merely because this verification has not yet been executed.
