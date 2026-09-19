# PrimeERP Global Gap Audit — 2026-09-19

## Scope
Initial audit snapshot was taken from `feature/salla-public-app-primeerp-20260919` (commit `8530c9bf40f4c9b0d8883addab1f37b205653426`). This branch now carries the follow-up global-gap implementation work. against the functional surfaces expected in mature ERP products such as Odoo, Microsoft Dynamics 365 Business Central, SAP Business One and Oracle NetSuite.

This is a product/architecture gap analysis, not a claim of feature parity.

## Current repository facts
- 2,880 tracked tree entries.
- 2,880 files/directories were inspected from the recursive tree; 220 test/spec-named files were identified.
- Backend has broad domains including accounting, audit, catalog, commerce, CRM, Egyptian e-invoice, enterprise, HR, integrations, inventory, manufacturing, POS, purchasing, reports, sales, shipping, SaaS, subscriptions, taxes, treasury and UOM.
- Frontend exposes a similarly broad module surface including accounting, approvals, assets, audit, commerce, CRM, HR, inventory, manufacturing, POS, purchasing, reports, reservations, restaurant, sales, shipping, treasury, workflow and others.
- A large portion of the tree is intentionally scaffolded (empty interface files/templates). These must not be treated as implemented business functionality.

## Priority classification
- P0: required before positioning PrimeERP as a dependable core ERP.
- P1: required for a strong production ERP.
- P2: differentiation/scale features after core completion.

## P0 — Core business integrity

### 1. Universal transaction/document lifecycle
Status: PARTIAL
Need one reusable lifecycle/state-transition engine for Sales, Purchase, Inventory, Payments, Journal, Expense, Production, Shipment, Returns and Contracts.
Required controls: allowed transitions, permissions, approval gates, idempotency, cancellation, reversal, immutable posted state, actor/time/reason audit.

### 2. Accounting posting engine
Status: PARTIAL
Need deterministic posting rules from operational documents to GL, with reversal/correction instead of mutation of posted entries.
Add/strengthen: recurring journals, reversing journals, accruals, deferrals, allocations, period controls, multi-currency revaluation, intercompany, dimensions/cost centers and posting diagnostics.

### 3. AR/AP end-to-end
Status: PARTIAL
Complete invoice -> receivable/payable -> payment -> allocation -> reconciliation -> aging -> statement -> GL.
Add credit/debit notes, write-off approval, residual calculation and automatic matching.

### 4. Bank/cash reconciliation
Status: PARTIAL — foundation implemented in this phase
Implemented in the current phase: bank accounts, statements, statement lines, reconciliation sessions, matching candidates, manual matching primitives, duplicate fingerprints, tenant/company scope and reconciliation APIs/UI. Remaining: bank fees/transfers accounting, richer tolerance/partner matching, immutable accounting linkage and full integration/E2E coverage.
Need statement import, matching rules, manual matching, unmatched queue, bank fees, transfers and reconciliation close.

### 5. Inventory/WMS integrity
Status: PARTIAL
Complete receipt, putaway, picking, packing, dispatch, transfer, returns, cycle count, adjustment, reservation and negative-stock policy.
Costing must be explicit and tested for FIFO, weighted average, standard/actual cost and inventory revaluation/adjustment.

### 6. Master Product/SKU engine
Status: PARTIAL — strengthened in this phase
Implemented in the current phase: commercial catalog identity binding for recipes, dedicated company-scoped Recipe SKU mappings, parent/variant recipe identity, Salla parent/variant SKU reconciliation, retry-on-failure for SKU-bearing Salla products, and concurrency-safe SKU binding. Remaining: supplier/channel mappings beyond Salla, packaging/accounting mappings, and full end-to-end database integration coverage.
SKU must be the stable identity across product, variants, barcode, UOM, price, tax, recipe/BOM, inventory, sales, purchasing, POS and external channels.
Add supplier mappings, channel mappings, packaging and accounting mappings.

### 7. Security and audit
Status: PARTIAL
Strengthen tenant/company/branch/warehouse/record scope; MFA/session controls; API keys; immutable audit history; before/after values; reason; actor; timestamp; source.

## P1 — Operational completeness

### 8. Sales
Complete quotation -> order -> reservation -> picking -> shipment -> delivery -> invoice -> payment -> AR -> GL -> profitability.

### 9. Purchasing
Complete RFQ -> quotation comparison -> PO -> approval -> receipt -> quality -> bill -> payment -> AP -> GL.

### 10. Manufacturing/MRP
Complete multi-level BOM, routing, work centers, capacity, material requirements, production orders, work orders, consumption, scrap/by-products, subcontracting and production costing.

### 11. CRM
Lead -> qualification -> opportunity -> activity -> quotation -> won/lost, with pipeline, forecast, salesperson, commission and customer 360.

### 12. POS/Restaurant
Complete POS session lifecycle, cash control, payments, refunds, discounts, stock/recipe consumption, shift close and accounting.
Restaurant requires recipe/menu, modifiers, kitchen flow, waste and food-cost integration.

### 13. Shipping/returns
Universal shipment lifecycle plus COD, carrier fee, commission, failed delivery, return-to-origin, reverse logistics, carrier settlement and reconciliation.

### 14. Integration Hub
Generalize Salla into a reusable integration platform: OAuth, webhooks, retries, idempotency, mapping, sync logs, dead-letter/replay, conflict handling and health monitoring.

### 15. HR/Payroll
Employee master, contracts, attendance, leave, overtime, allowances, deductions, loans, payroll calculation, statutory rules and GL posting.

### 16. Reporting/BI
Build operational, financial and executive analytics with drill-down to source transactions. Add scheduled reports, exports, dashboards and KPI definitions.

### 17. Universal workflow/approvals
One workflow engine reused by financial, operational and master-data documents, with conditional routing, multi-level approvals and delegated approval.

## P2 — Enterprise/global differentiation

### 18. Localization engine
Country adapters for tax, e-invoice, fiscal rules, payroll and reporting. Egypt should be the first adapter, not hard-coded into the platform.

### 19. AI layer
Move from assistant/report generation to explain, detect, forecast, recommend and (with approval) execute actions.

### 20. Mobile execution
Warehouse scanning, sales, approvals, stock counts, deliveries, field activities and management alerts.

### 21. Developer/extensibility platform
Stable API versioning, webhooks, custom fields, custom reports, event subscriptions, app/add-on model and integration credentials.

### 22. Enterprise finance
Consolidation, intercompany elimination, multi-entity close, advanced budgeting/forecasting and financial consolidation.

## Recommended completion order

1. Universal transaction lifecycle
2. Accounting posting + period controls
3. AR/AP + reconciliation
4. Product/SKU/UOM/tax master data
5. Inventory/WMS + costing
6. Sales end-to-end
7. Purchasing end-to-end
8. Payments/Treasury + bank reconciliation
9. Manufacturing/MRP + Recipe/BOM
10. POS/Restaurant
11. Shipping/returns + carrier settlement
12. Integration Hub + Salla
13. CRM
14. HR/Payroll
15. Workflow/Approvals
16. BI/Reports
17. Localization engine
18. AI
19. Mobile
20. Developer platform

## Definition of Done for every module

A module is NOT considered complete because its router/model/page exists.

It is complete only when all applicable layers exist:
- Database/migrations
- Domain rules
- API
- Permissions
- Tenant/company scope
- UI
- Validation
- Workflow/status transitions
- Accounting impact
- Inventory impact
- Audit trail
- Idempotency/retry behavior
- Error handling
- Unit tests
- Integration tests
- End-to-end test
- Documentation

## Architectural rule

Do not add another large module until its upstream/downstream business loop is connected and tested.

PrimeERP should optimize for end-to-end transaction integrity and operational usability rather than raw module count.
