# PrimeERP Full-System Audit and Completion Plan
Date: 2026-10-20
Base: feature/azul-ui-saas-20260923
Working branch: feature/primeerp-full-system-audit-20261020-v2

## Status vocabulary
- VERIFIED: code plus automated tests prove behavior; runtime status recorded separately.
- IMPLEMENTED_UNVERIFIED: code exists but tests/runtime checks have not passed.
- PARTIAL: one or more required layers or business paths are missing.
- CONFIGURATION_REQUIRED: code exists but provider/device credentials or external setup are needed.
- NOT_FOUND: no implementation found after repository-wide search.
- BLOCKED: source/runtime access prevents reliable verification.

## Safety rules
- Never modify a frozen release branch or run production migrations as part of audit.
- Never commit credentials, access tokens, biometric templates, or real employee/customer/vendor data.
- A feature is complete only when UI, API, authorization, persistence, business rules, audit trail, tests and downstream effects are verified.
- Hardware/provider tests must be labeled NOT RUNTIME-VERIFIED until executed on a real test device or sandbox.
- External connectors must be tenant-scoped, least-privilege, encrypted, idempotent, observable, retryable and revocable.

## Accounting submodules
1. General Ledger: chart of accounts, journals, posting/reversal, recurring journals, periods, trial balance.
2. AR: invoices, credit notes, receipts, allocations, ageing and write-offs.
3. AP: supplier bills, debit notes, payment runs, allocations and ageing.
4. Treasury: cashboxes, banks, transfers, cheques, deposits and bank reconciliation.
5. Tax: tax codes/rates/effective dates, VAT, withholding tax and returns.
6. Fixed Assets: register, capitalization, depreciation, transfers, disposals and GL integration.
7. Cost Accounting/Budgets: cost centres, dimensions, allocations and budget-vs-actual.
8. Financial Reporting: P&L, balance sheet, cash flow and subledger-to-GL reconciliation.
Invariants: balanced double-entry, immutable posted entries, corrections by reversal, open-period checks, company/branch authorization and idempotent posting.

## HR / Workforce / Payroll submodules
1. Employee master, contracts, departments, positions, grades, reporting lines and lifecycle.
2. Recruitment, onboarding/offboarding, documents and expiry reminders.
3. Attendance: shifts, rosters, holidays, breaks, overtime, lateness, missed punches, corrections and approvals.
4. Biometric device gateway: vendor-neutral adapters, device registry/health, encrypted credentials, event ingestion, unique device event IDs, duplicate suppression, clock-drift/time-zone handling, offline buffering, retries, employee mapping and exception reconciliation.
5. Leave: entitlements, accruals, carry-over, requests, approvals and payroll impact.
6. Payroll: salary structures, allowances, deductions, overtime, advances, statutory rules configurable by jurisdiction, retroactive adjustments, payslips, bank exports and GL posting.
7. Employee self-service, manager approvals, performance, training, skills and certifications.
8. Reports and statutory exports.
Privacy: prefer storing fingerprint templates on the device. Do not centralize raw biometric data without legal/privacy review, purpose limitation, encryption, retention/deletion rules and tightly restricted access. Punches must not directly alter payroll without traceable rules and approvals.

## Commerce and operations
- CRM lead/opportunity/quote -> sales order -> reservation -> delivery -> invoice -> receipt -> reconciliation -> GL.
- Procurement request/RFQ -> approval -> PO -> receipt/quality -> supplier bill -> payment -> GL.
- Catalog, variants, barcode, UOM, price lists, discounts and tax.
- Inventory: multi-company/branch/warehouse/bin, transfers, reservations, counts, serial/batch/expiry, landed cost, costing and stock-to-GL.
- POS: session lifecycle, payments, returns, offline queue, idempotent replay, EOD reconciliation, inventory and accounting.
- WMS/SCM: receiving, putaway, pick/pack/ship, carrier events and proof of delivery.
- Salla/e-commerce: OAuth, signed webhooks, replay protection, order/payment/shipping synchronization and dead-letter review.

## Other modules to inventory
Projects/tasks/timesheets; contracts/commercial leasing; hospitality/property operations; fleet/maintenance; manufacturing/BOM/MRP/quality; document management/e-signature; helpdesk; mobile/offline; marketing; AI reporting/forecasting; SaaS subscriptions/entitlements; jurisdiction and e-invoicing.

## Security release blockers
- Tenant/company/branch scope on every API, file, export, job and webhook; negative cross-tenant tests.
- Authentication/session revocation, MFA options, password reset, brute-force/rate limits.
- Backend permissions by module/action/company/branch/amount and sensitive field.
- Input validation, safe uploads, output encoding, SSRF defenses, CSRF/CORS/cookie review.
- Secret scanning, dependency scanning, strong production config, encryption/key rotation.
- Audit sensitive mutations, approvals, exports and integration actions without leaking secrets or unnecessary PII.
- Backups, restore drill, monitoring, incident runbook, CI gates and migration graph checks.

## Integration registry requirements
For every external system record provider, purpose, data direction/events, credential scopes, signature verification, refresh/revocation, rate limits, idempotency key, retries/backoff, dead-letter handling, sync cursor, mapping/versioning, health/last-success, reconciliation and sandbox tests.
Assess only when supported by the code/business requirements: Egyptian ETA e-invoice, email/SMTP, SMS/WhatsApp, payment gateways, bank files/APIs, Salla/e-commerce, shipping carriers, biometric terminals, barcode/label printers, SSO/identity, storage, AI providers and generic webhooks. Do not claim compatibility until adapter contracts and tests exist.

## End-to-end acceptance journeys
1. Purchase: request -> approval -> PO -> receipt -> bill -> payment -> bank reconciliation -> GL -> reports.
2. Sale: quote -> order -> stock -> shipment -> invoice -> receipt -> GL -> reports.
3. POS: open session -> sale/payment -> stock and GL -> close session -> EOD variance; replay never duplicates.
4. HR: employee -> shift -> biometric punches -> exception approval -> attendance -> payroll preview/approval -> payslip -> GL.
5. Treasury: cheque lifecycle -> balanced journal -> reversal/return -> bank reconciliation.
6. Inventory: transfer/count/return/expiry -> costing -> GL valuation tie-out.
7. Security: tenant A cannot access tenant B through UI/API/export/files/jobs/webhooks.

## Required deliverables
- Module inventory mapping UI route, API, service, model, migration, permission, tests and integration.
- Dependency map/business-event contracts.
- Critical/High/Medium/Low security findings and fixes.
- Automated E2E tests with expected ledger/inventory balances.
- Single deterministic Alembic head and clean-PostgreSQL migration test.
- Backend tests, frontend lint/typecheck/build, dependency/secret scan results.
- Runtime/device/provider checklist and final pull instructions.

Docker/runtime is currently unavailable by user instruction. This document is a plan, not proof that each listed capability is implemented.