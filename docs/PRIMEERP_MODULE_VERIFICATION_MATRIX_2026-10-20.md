# PrimeERP Module Verification Matrix
Date: 2026-10-20
This is an initial triage based on source inspection and GitHub development history, not a claim that all modules are complete.

| Domain | Evidence observed | Verification needed |
|---|---|---|
| Accounting / GL | JournalService and journal posting module exist | balanced posting, reversal, periods, idempotency, permissions, financial statements |
| AR/AP | commerce models include sales/purchase documents, payment allocations | full invoice/payment/ageing/reconciliation journeys |
| Treasury | cheque lifecycle and TreasuryAccountingService integration PR exist | all transitions, company/tenant scope, reversals, bank reconciliation |
| Tax / ETA | tax identity fields and ETA document service exist | Egyptian ETA sandbox, signature/payload validity, token rotation, idempotency, filing totals |
| Inventory / costing | item, stock move, transfer, reservation and costing modules exist | concurrency, partial fulfillment, returns, costing, negative stock policy and GL tie-out |
| Sales / purchasing | commerce routes and document models exist | quote/order/delivery/invoice/payment and request/PO/receipt/bill/payment E2E |
| POS | router, UI, outlet/session/order/payment, offline-first work exists in branch history | offline replay, duplicate prevention, payment mappings, stock/GL/EOD reconciliation |
| HR / workforce | current HR router only exposes tenant-user workforce list/profile update; separate enterprise Employee/Payroll models exist | employee lifecycle, company-scoped employee records, attendance, leave, payroll approval, GL, statutory setup |
| Biometrics | no device gateway verified in inspected HR code | vendor-neutral adapter, device registry, signed/authenticated event ingestion, duplicate suppression, offline retry, drift, mapping, privacy |
| SaaS / tenants | plan, subscription, entitlement modules and plan-sync work exist | enforce limits server-side across all paths, subscription races, tenant isolation |
| Salla / shipping | Salla public app, integration and shipping lifecycle code exists | OAuth/webhook security, replay, retry/dead-letter, mapping and reconciliation |
| CRM / AI reports | CRM and report/AI automation surfaces exist | source-data permissions, factual accuracy, data isolation, failure handling |
| Enterprise operations | fixed assets, budgets, projects, contracts and basic payroll models/routes exist | depreciation GL posting, budget-vs-actual integrity, employee/payroll lifecycle, contract/project accounting |
| Documents / approvals / audit | audit module, legal module, approval foundations are present | universal workflow coverage, tamper resistance, retention, signature provider and audit PII minimization |
| Manufacturing / WMS / mobile / helpdesk | module routes or code surfaces exist | actual process depth, access checks, inventory/GL linkage and operational E2E |

## Specific security gap fixed in this branch
The HR workforce profile endpoint previously accepted profile updates without an explicit action-level permission and without a company context on the mutation. This branch adds a permission dependency, validates company membership in the current tenant, validates profile fields, rejects unknown fields, records an audit event containing changed field names only, and updates the UI to pass company_id. Automated CI is still required to verify the change.

## Known work that remains open
- HR is not yet a complete HCM/attendance/payroll system; current workforce endpoint edits user profile fields, while enterprise Employee/Payroll are separate basic models/routes.
- Biometric integration is not yet verified and must be designed as a connector gateway, not a vendor-specific assumption.
- POS PR history explicitly included later hardening after initial known gaps; final status must be tested on this branch.
- Repository history has parallel feature branches; merge/release readiness requires confirming the target branch and migration graph before integrating divergent tax/release changes.
- Hardware, ETA, payment, bank, Salla and carrier integrations require test credentials/devices and cannot be declared runtime-verified from source alone.

## Exit criteria
Every module must have UI/API/service/model/migration/permission/test mapping; main and failure/retry paths; tenant isolation tests; audit and idempotency; cross-module ledger/stock assertions; clean migration tests; and explicit configuration/runtime status for external integrations.


## Follow-up hardening (2026-10-22)

Source review on the working branch made these additional corrections:

- Replaced direct authenticated-user tenant lookups with the request's effective tenant across accounting, commerce, commissions, inventory adjustments/costing/locations/reservations/stock moves/transfers/warehouses, integrations, jurisdiction, developer APIs, POS, branches and HR. Active-company checks are now enforced in these company-scoped helpers.
- Applied the same effective-tenant and active-company rule to treasury reconciliation, shipping settlements and Egyptian e-invoicing operations.
- Restricted manufacturing BOM access to inventory access plus manufacturing and inventory entitlements; material issue posting additionally requires inventory write and post permissions.
- Restricted AI financial advice to users with accounting access and the accounting entitlement.
- The fixed-asset depreciation endpoint now fails closed because the current asset model has no depreciation account mapping, posting history or GL journal workflow. It no longer changes accumulated depreciation without a corresponding ledger entry.

These are source-level corrections only. Automated tests, database migrations, frontend checks and provider/device runtime journeys have not been run or confirmed. The broader module-completion and E2E criteria above remain open.
