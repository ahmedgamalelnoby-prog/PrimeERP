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
| Settings and workflow | Configurable applications, access rights, automated actions (capabilities vary by edition) | Configurable best-practice processes, extensibility and role-based access | Company settings registry has 75 keys (68 runtime / 7 catalog-only at this branch head). Unit tests cover helper decisions for catalog-only HR/POS/approval settings but do not prove connectors or workflows end-to-end. The original five remain catalog-only: `hr.attendance_source`, `hr.biometric_sync_interval_minutes`, `workflow.approval_mode` and `workflow.escalation_after_hours`, `pos.allow_open_cash_drawer`. Reporting now has a dedicated category: `reports.allow_scheduled_delivery` is enforced at schedule creation and `reports.default_export_format` supplies the default JSON/text format; `reports.max_export_rows` and `reports.include_filters_in_export` remain catalog-only because tabular export consumers are not implemented. Other runtime-marked settings still require consumer-by-consumer integration tests. |
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
10. Bind each setting to validated APIs, audit history, permission checks and the business workflow consuming it. Settings Center category links now route to the company-policy registry; a dedicated `Reporting` registry category now exists with four export/scheduling preferences, all explicitly catalog-only until actual export/scheduler consumers and integration tests are implemented.

### P2 — enterprise breadth
11. Add fixed asset register/depreciation/disposal, budget planning and variance, project accounting/profitability, service contracts/SLA, maintenance scheduling, document management/retention and approval delegation.
12. Add enterprise data migration/import validation, master-data deduplication, reconciliation workbench, API versioning and connector observability.
13. Add operational dashboards, configurable KPIs, report scheduling/delivery, row-level data scopes and export auditing.
14. Document role templates, segregation-of-duties conflicts, disaster recovery targets and a repeatable security threat model.

## Changes made in this branch

- Legacy `/accounting/reports` redirects to `/reports/financial`.
- Legacy `/shipping/reconciliation` redirects to `/reports/shipping/reconciliation`.
- Removed Carrier Reconciliation from the Shipping navigation group so it is not exposed as a separate shipping menu item; the report remains in the central Reports navigation/route.
- Settings Center links for accounting, commerce, inventory, HR, approvals, messaging and security now select the corresponding category in the company-policy screen. Reporting settings now route to a dedicated `Reporting` policy category. Four preferences were added: scheduled delivery is disabled by default and is enforced at schedule creation; default format is consumed by the scheduler and supports only the existing JSON/text worker contract; row limits and export filter metadata remain catalog-only until tabular export consumers exist. The financial AI analysis endpoint additionally requires `accounting.access`.
- Added unit tests for attendance-source matching, biometric interval decisions, approval-plan semantics, escalation thresholds and cash-drawer policy decisions. These test the helpers only; no connector, scheduler, multi-approver persistence, escalation delivery or physical cash-drawer endpoint was invented to make a catalog-only policy appear operational.

These are routing/architecture improvements, not proof that every Odoo/SAP capability has been implemented. No database changes or destructive operations are included. Build and test status must be verified in the local environment/CI before merging.

## Public references

- Odoo application suite overview: https://github.com/odoo/odoo
- SAP S/4HANA Cloud business areas: https://help.sap.com/docs/SAP_S4HANA_CLOUD/9d794cbd48c648bc8a176e422772de7e/e237c247cc454f1b8307e52d0624d0f4.html
- SAP S/4HANA Cloud product scope: https://learning.sap.com/products/s4hana-cloud


## Reporting follow-up — 2026-10-24

- The company-policy registry now contains 75 keys: 68 marked runtime and 7 catalog-only. The runtime label is a source-level consumer classification; the self-hosted Release Gate remains queued, so no test-pass claim is made.
- Scheduled report creation now checks the company-specific `reports.allow_scheduled_delivery` switch and returns HTTP 409 when disabled. The default is false to avoid unexpected outbound delivery.
- If a schedule omits its format, the API resolves `reports.default_export_format`; supported formats are JSON and text, matching the current worker. Explicit supported formats are preserved.
- The financial AI analysis endpoint now enforces `accounting.access` as well as the Reports module entitlement because it reads accounting records.
- `reports.max_export_rows` and `reports.include_filters_in_export` remain catalog-only until tabular export paths exist; no non-existent export functionality is claimed.


## Module-aware report visibility — 2026-10-24 follow-up

- The central Report Center now filters each report entry by its owning module's enabled entitlement, hides empty groups, and retains the platform-administrator override.
- This is a navigation/visibility improvement, not the authorization boundary: each backend report endpoint must still enforce source-module permissions and tenant/company scoping. The financial AI analysis endpoint specifically requires `accounting.access` in addition to the Reports module entitlement.
- Frontend typecheck/build and backend tests are still pending the self-hosted Release Gate; this UI change is not claimed as verified until that run completes.


## Scheduled report policy enforcement — 2026-10-24 follow-up

- The scheduled-report worker now re-reads `reports.allow_scheduled_delivery` immediately before processing each due delivery. A disabled, malformed, or unreadable policy fails closed: the delivery is paused, its next-run time is cleared, and the worker does not create a delivery attempt or send a message.
- Added a company-scoped `POST /reports/schedules/{delivery_id}/resume` endpoint. It verifies tenant/company ownership, re-checks the scheduling policy, validates the stored format, and calculates the next run before reactivating a paused schedule.
- The Report Center's hero action is now hidden when the user lacks the Reports module entitlement, matching the existing module-aware report-card filtering. Backend entitlement checks remain authoritative.
- Added unit tests for worker pause behavior when the policy is false or cannot be read. Tests and Release Gate remain unconfirmed until the self-hosted run completes.


### Approval policy wiring update (2026-10-24)

- The generic approval-request endpoint already consumes `workflow.approval_mode`; payroll submission now consumes the same company policy rather than hard-coding sequential approval. The registry marks the policy runtime, with tests for all supported modes and invalid values.
- The approval escalation worker consumes `workflow.escalation_after_hours` to queue idempotent in-app reminders for pending approval steps; the registry now marks this policy runtime. This does not claim external email/WhatsApp escalation or prove the worker has passed integration tests.
- The current catalog-only list is now five settings: `hr.attendance_source`, `hr.biometric_sync_interval_minutes`, `pos.allow_open_cash_drawer`, `reports.max_export_rows`, and `reports.include_filters_in_export`.
