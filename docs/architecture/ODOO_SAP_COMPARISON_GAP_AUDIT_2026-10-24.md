# PrimeERP comparison and gap audit — 2026-10-24

## Purpose and limits

This is a capability-gap baseline for PrimeERP against publicly documented Odoo applications and SAP S/4HANA business scope. It is not a claim that feature names in PrimeERP imply complete business workflows. A capability is considered implemented only when its UI, API/service, persistence, authorization, tenant boundary, workflow effects, and automated tests are evidenced together. This first audit is repository-informed but is not a full source-code or runtime certification.

Reference scope:
- Odoo public application suite: CRM, sales, accounting, inventory, manufacturing, project management, HR, website/eCommerce and related apps.
- SAP S/4HANA Cloud public scope: finance, sourcing/procurement, sales, supply chain, manufacturing, asset management, service, professional services and analytics.
- PrimeERP current repository has modules for accounting, treasury, sales, purchasing, inventory, CRM, HR, POS, manufacturing, hospitality, commercial leasing, shipping, SaaS administration, reports, settings, integrations, and platform/identity. Some frontend routes intentionally use a generic ModuleWorkbench/Operational/ComingSoon screen; those are not proof of full module implementation.

## Comparison matrix

| Capability area | Odoo baseline | SAP S/4HANA baseline | PrimeERP repository evidence / gap |
|---|---|---|---|
| Finance and controlling | Accounting, invoicing, payments, analytic accounting | General ledger, close, receivables/payables, cost/profitability, treasury/risk | Accounting, treasury and financial-report pages exist. Verify end-to-end subledger-to-GL posting, period close, reconciliations, FX revaluation, budgets, audit trails and financial statement tie-outs. |
| Sales and order-to-cash | CRM, quotations/orders, invoicing, POS/eCommerce | Quotes/contracts/orders, delivery, billing, returns, rebates and analytics | Sales/CRM/POS routes exist. Validate pricing/discount authorization, credit checks, delivery-to-invoice rules, returns/credit notes, rebates and complete accounting integration. |
| Procurement and procure-to-pay | Purchase, vendor bills, inventory integration | Sourcing, contracts, purchasing, invoice management and procurement analytics | Purchasing pages and company policies exist. Validate requisitions/RFQ comparisons, PO/receipt/invoice matching, tolerance controls, vendor performance and duplicate invoice prevention. |
| Inventory and warehouse | Stock, multi-warehouse, barcode, replenishment | Inventory, warehouse, availability/ATP, transport integration | Inventory, transfers, reservations and warehouses exist. Validate bin/lot/serial/expiry, costing, physical counts, replenishment/MRP, inter-warehouse valuation and race-safe reservations. |
| Manufacturing and quality | Manufacturing orders, BOM, maintenance apps | Production planning, quality, EHS, product engineering | Manufacturing route exists; need verify BOM/routings, capacity planning, material requirements, WIP/cost roll-up, scrap/by-products, quality inspection and traceability. |
| HR and payroll | Employees, time off, expenses and HR apps (some advanced capabilities vary by edition) | Workforce/time capabilities and integrations; broader HR often delivered with connected SAP solutions | HR route and policy catalog exist. Verify employee lifecycle, contracts, payroll calculations, statutory rules, leave accrual, attendance/biometric device integration, overtime, approvals and payroll-to-GL. |
| Projects, assets, service and maintenance | Project management, timesheets, maintenance, field service and fleet apps | Project/service management, asset maintenance and resource scheduling | Enterprise/project/assets/service coverage must be checked individually; generic workbench routes are not complete proof. Add asset lifecycle/depreciation, preventive maintenance, service contracts/SLA, time/cost capture and project profitability where absent. |
| Hospitality, leasing and shipping | Odoo supports rental, POS, subscriptions and configurable apps; industry-specific hotel scope may need extensions | Industry/process extensions and connected solutions depending on scope | PrimeERP has hospitality, leasing and shipping routes. Differentiate real operating workflows from workbench placeholders; test contract billing, occupancy/revenue share, installment schedules, carrier invoices/settlements and reconciliation. |
| Reporting and analytics | Application reports, dashboards, exports, app integrations | Embedded analytics and process analytics | Central report center exists, but several links are placeholders. Only financial reports and shipping reconciliation currently have known target pages from this branch; remaining report pages/APIs and backend authorization require implementation. Legacy URLs now redirect to central Reports. |
| Settings and workflow | Configurable applications, access rights, automated actions (capabilities vary by edition) | Configurable best-practice processes, extensibility and role-based access | Company settings registry has 71 keys and consumer tests; registry test explicitly identifies five catalog-only settings: `hr.attendance_source`, `hr.biometric_sync_interval_minutes`, `workflow.approval_mode`, `workflow.escalation_after_hours`, `pos.allow_open_cash_drawer`. Other runtime-marked settings still require consumer-by-consumer verification and integration tests. |
| Security and governance | Access groups/rules, application-level permissions | Role/business catalogs, enterprise authorization and governance controls | Identity/roles/permissions, tenant-boundary tests and company policy infrastructure exist. Must verify server-side authorization on every report/export/API, company/branch isolation, object-level checks, audit log immutability, secret handling, MFA/session controls and security regression coverage. |
| Integration and extensibility | App ecosystem, APIs, external integrations | SAP integration suite/ecosystem and defined extension points | Integration module and retry/sync policies exist. Verify idempotency, signatures, replay prevention, dead-letter/retry handling, mapping/versioning, webhook observability, rate limits and end-to-end connector contract tests. |
| Platform operations | Odoo hosting/upgrade options vary by edition | SAP cloud/on-premise/private-cloud operating models | PrimeERP Docker/migrations/workers are present. Add tested backup/restore, migration rollback strategy, health/readiness checks, queue recovery, observability, release CI, dependency/security scans and documented disaster recovery. |

## Prioritized backlog

### P0 — correctness, security, and financial integrity
1. Build a route-to-permission inventory and enforce authorization in backend handlers/services, not only navigation. Include exports, scheduled reports, report downloads and direct URLs.
2. Add tenant/company/branch isolation tests for every domain query and mutation, including background workers and report jobs.
3. Verify accounting invariants: balanced journal entries, idempotent posting, immutable posted documents, controlled reversals, closed-period protection and deterministic numbering.
4. Complete procure-to-pay and order-to-cash integration tests, including duplicate invoice, partial receipt/delivery, return, cancellation, tax and below-cost/credit-limit edge cases.
5. Add CI gates for frontend typecheck/build, backend tests/migrations, dependency scanning and migration validation.

### P1 — complete business workflows
6. Complete the five catalog-only settings above only when the owning workflow and integration are real; otherwise keep them explicitly non-operational in UI.
7. Complete HR attendance source/biometric synchronization and payroll approval-to-GL with device failure/replay and payroll-period locking tests.
8. Complete manufacturing BOM/routing/MRP/WIP/quality and inventory valuation/cost roll-up.
9. Implement report pages/services for every advertised report card; remove or disable any link until an actual page/API exists. Keep all report entry points in central Reports and apply source-module plus report-level permissions server-side.
10. Make Settings section links select the requested section, and bind each setting to validated APIs, audit history, permission checks and the business workflow consuming it.

### P2 — enterprise breadth
11. Add fixed asset register/depreciation/disposal, budget planning and variance, project accounting/profitability, service contracts/SLA, maintenance scheduling, document management/retention and approval delegation.
12. Add enterprise data migration/import validation, master-data deduplication, reconciliation workbench, API versioning and connector observability.
13. Add operational dashboards, configurable KPIs, report scheduling/delivery, row-level data scopes and export auditing.
14. Document role templates, segregation-of-duties conflicts, disaster recovery targets and a repeatable security threat model.

## Changes made in this branch

- Legacy `/accounting/reports` redirects to `/reports/financial`.
- Legacy `/shipping/reconciliation` redirects to `/reports/shipping/reconciliation`.
- Removed Carrier Reconciliation from the Shipping navigation group so it is not exposed as a separate shipping menu item; the report remains in the central Reports navigation/route.

These are routing/architecture improvements, not proof that every Odoo/SAP capability has been implemented. No database changes or destructive operations are included. Build and test status must be verified in the local environment/CI before merging.

## Public references

- Odoo application suite overview: https://github.com/odoo/odoo
- SAP S/4HANA Cloud business areas: https://help.sap.com/docs/SAP_S4HANA_CLOUD/9d794cbd48c648bc8a176e422772de7e/e237c247cc454f1b8307e52d0624d0f4.html
- SAP S/4HANA Cloud product scope: https://learning.sap.com/products/s4hana-cloud
