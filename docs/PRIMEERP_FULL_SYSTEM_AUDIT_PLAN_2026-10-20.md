# PrimeERP Full-System Audit & Completion Plan

Date: 2026-10-20
Base: feature/product-completion-final-tax2
Working branch: feature/primeerp-full-system-audit-20261020

## Safety and execution rules

- This branch is additive and must not modify a frozen release/RC branch.
- Do not run production migrations, reset databases, delete business records, or publish external integrations as part of static audit.
- Never commit credentials, access tokens, biometric templates, employee personal data, or real customer/vendor data.
- Treat a feature as complete only when its UI, API, authorization, persistence, business rules, audit events, tests, and cross-module effects are verified.
- Mark anything not exercised against a running database/device/provider as NOT RUNTIME-VERIFIED, not complete.
- External integrations must be opt-in, tenant-scoped, encrypted at rest, least-privilege, idempotent, observable, and safely retryable.

## Completion status vocabulary

- VERIFIED: code and automated tests prove the behavior; runtime checks are recorded separately.
- IMPLEMENTED_UNVERIFIED: implementation exists but the required tests/runtime checks have not passed.
- PARTIAL: some layers or business paths exist, but at least one required path is missing.
- CONFIGURATION_REQUIRED: integration exists but needs customer secrets/device/provider configuration.
- NOT_FOUND: no implementation found after repository-wide search.
- BLOCKED: cannot verify because repository/runtime/provider access is unavailable.

## Release-blocking audit tracks

### A. Platform foundation and security
- Tenant/company/branch scoping on every read and write; negative tests against cross-tenant IDs.
- Authentication/session expiry, refresh/revocation, MFA options, password reset, brute-force controls and rate limiting.
- Server-side permission checks at module, action, company, branch, amount threshold and sensitive-field level.
- Input validation, safe file uploads, output encoding, SSRF protection for webhook/import URLs, SQL/ORM safety.
- Secrets out of source/logs; encryption/key rotation; secure cookie/CORS/CSRF policy as applicable.
- Immutable audit trail for sensitive changes, approval actions, exports, login events and integration operations.
- Dependency/security scanning, SBOM, secret scanning, reproducible CI, backup/restore drills and incident runbook.

### B. Accounting, split into bounded submodules
1. General Ledger: chart of accounts, journals, posting/reversal, recurring journals, periods, trial balance.
2. Accounts Receivable: customer invoices/credit notes, receipts, allocations, ageing, write-offs.
3. Accounts Payable: supplier bills/debit notes, payment runs, allocations, ageing.
4. Cash & Treasury: cashboxes, banks, transfers, cheques, deposits, bank reconciliation.
5. Tax: tax codes/rates/effective dates, VAT, withholding tax, tax reports/returns and audit history.
6. Fixed Assets: register, capitalization, depreciation books, transfers, disposals, impairment and GL integration.
7. Budgeting & Cost Accounting: budgets, cost centres, dimensions, allocations, budget-vs-actual.
8. Financial Reporting: trial balance, P&L, balance sheet, cash flow, subledger-to-GL reconciliation.
Invariants: posted entries balance; posted entries are immutable; corrections use reversals; period/company/branch/account permissions are enforced; posting is idempotent; source documents reconcile to GL.

### C. People / HR / Workforce / Payroll
1. Employee master, contracts, departments, positions, grades, reporting lines and employee lifecycle.
2. Recruitment, onboarding/offboarding, documents, expiry reminders and equipment/access handover.
3. Attendance & Time: shifts, rosters, holidays, lateness, overtime, breaks, missing punches, corrections and approvals.
4. Biometric/device gateway: vendor-neutral adapter interface; device registry; encrypted credentials; device health; pull/push event ingestion; unique event IDs; duplicate suppression; time-zone/device-clock drift handling; offline buffering; retries; device-to-employee mapping; manual exception queue; reconciliation and audit.
5. Leave: balances, accrual rules, carry-forward, requests, approvals, holidays and payroll impact.
6. Payroll: salary structures, allowances, deductions, overtime, loans/advances, tax/social insurance configuration, retroactive adjustments, payslips, bank file/export and GL posting.
7. Employee self-service, manager approvals, performance, training, skills/certifications, disciplinary records with strict access control.
8. HR reports and statutory exports configurable by jurisdiction.
Biometric privacy: store vendor templates on the device where possible; avoid central storage of raw fingerprints; if a template must be stored, use encryption, strict purpose limitation, retention/deletion controls and explicit legal/privacy review. Attendance events must not directly modify payroll without reviewable rules and approvals.

### D. Commercial operations
- CRM leads/opportunities/activities/quotations and conversion to orders.
- Sales order, reservation/allocation, shipment/delivery, invoice, receipt, return/credit note and GL.
- Procurement request/RFQ/approval/PO/receipt/quality/ supplier invoice/payment/GL.
- Product/catalog/variants/barcodes/UOM/pricelists/discounts/tax and effective dating.
- Inventory multi-company/branch/warehouse/bin, transfers, reservations, counts, batches/serials/expiry, landed cost, costing and stock-to-GL reconciliation.
- POS: session lifecycle, offline queue, idempotent replay, payments, returns, cash/card/bank settlement, EOD reconciliation, inventory and accounting.
- WMS/SCM: receiving, putaway, pick/pack/ship, carrier events, proof of delivery and shipment cost.
- Salla/e-commerce/webshop integrations: OAuth lifecycle, webhooks, replay protection, mapping, order/payment/shipping sync, retries and dead-letter review.

### E. Other business modules
Audit implementation and decide explicitly whether to implement, integrate, or defer: projects/tasks/timesheets; contracts/commercial leasing; hospitality/property operations; fleet/maintenance; fixed assets; document management/e-signature; service desk/helpdesk; manufacturing/BOM/MRP/quality; budgeting; CRM/marketing; mobile/offline workflows; AI reports/forecasting. Never present a module as complete based on navigation or CRUD screens alone.

### F. Integrations inventory
Maintain a registry for each connector: purpose, provider, owner, supported direction/events, credential scopes, webhook signature, token refresh/revocation, rate limits, idempotency key, retry/backoff, dead-letter handling, sync cursor, mapping/versioning, health/last-success, reconciliation, tenant isolation and test mode.
Candidates to assess from actual repo/configuration: email/SMTP, SMS/WhatsApp, payment gateways, banks/import formats, e-invoice/tax authority, Salla/e-commerce, shipping carriers, biometric attendance devices, barcode/label printers, accounting imports/exports, storage, identity/SSO, analytics/AI providers and webhooks. Do not claim provider compatibility until adapter contracts and tests exist.

## Required audit artifacts
- Module inventory: UI routes, API routes, services, models, migrations, permissions, tests and integration dependencies.
- Module dependency map and business-event contracts.
- Security threat model and findings ranked Critical/High/Medium/Low.
- Cross-module E2E scenarios with test data and expected accounting/inventory balances.
- Migration graph/head check and clean-database migration test.
- CI results for backend tests, frontend lint/build, migration tests, dependency/secret scans.
- Runtime smoke checklist to execute when the user's machine is available.
- Final pull request summary with implemented changes, unresolved blockers, and exact pull commands.

## End-to-end acceptance journeys
1. Purchase: request -> approval -> PO -> receipt -> supplier bill -> payment -> bank reconciliation -> GL -> reports.
2. Sale: quote -> order -> stock allocation -> shipment -> invoice -> receipt -> reconciliation -> GL -> reports.
3. POS: open session -> sale/payment -> stock deduction -> GL -> close session -> EOD variance reconciliation; repeat replay must not duplicate effects.
4. HR: employee -> assigned shift -> biometric punches -> exception approval -> attendance calculation -> payroll preview/approval -> payslip -> GL posting.
5. Treasury: cheque lifecycle -> accounting event -> balanced journal -> reversal/return handling -> bank reconciliation.
6. Inventory: transfer/count/return/expiry -> costing -> GL valuation tie-out.
7. Security: tenant A cannot read/write tenant B data through UI, API, exports, files, background jobs or integration callbacks.

## Current limitations
The Docker environment is unavailable by user instruction. Runtime/device/provider checks therefore remain pending. Before changing production code, the repository files and active branch must be readable and the current branch head must be confirmed. This plan is not evidence that the listed modules or controls are already implemented.
