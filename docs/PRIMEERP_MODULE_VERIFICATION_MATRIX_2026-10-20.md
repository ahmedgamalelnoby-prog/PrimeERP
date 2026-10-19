# PrimeERP Module Inventory and Verification Matrix

Date: 2026-10-20
Status: initial evidence-based triage; not a claim of completion.

Legend:
- IMPLEMENTATION SIGNAL: a GitHub PR or repository history explicitly indicates code was added.
- VERIFY: must inspect current branch files and tests before assigning a completion status.
- BLOCKED: cannot be runtime-verified while the local environment is unavailable.

| Domain | Implementation signal from repository history | Required verification before marking complete |
|---|---|---|
| Accounting / GL | Broad accounting architecture and universal transaction controls referenced in PR #23; Treasury-to-GL service described in PR #30 | journal balancing, immutable posted entries, reversal, periods, dimensions, permissions, source idempotency, trial balance and statements |
| Treasury / Cheques | PR #30 describes cheque lifecycle mappings and central JournalService integration | all lifecycle transitions, company/tenant isolation, reversal correctness, bank reconciliation and duplicate event tests |
| Tax / E-invoice | tax-related release convergence in PR #11; product-completion branch history | rates/effective dates, VAT/WHT calculations, return totals, tenant constraints, invoice idempotency and jurisdictional requirements |
| Inventory / Costing | FIFO/cost layers and inventory audit referenced in PR #23; gaps mentioned in PR #29 | negative stock policy, concurrent reservations, partial fulfillment, returns, cost layers, landed cost and stock-to-GL tie-out |
| Sales / Orders | Broad sales and commerce domain in PR #18/#25 history | quote-to-order-to-delivery-to-invoice-to-receipt-to-GL; credit notes, taxes, discounts and idempotency |
| Purchasing / AP | Broad purchasing domain in PR #18/#25 history | requisition-to-PO-to-receipt-to-bill-to-payment-to-GL; partial receipts, price/quantity variance and approvals |
| POS | POS domain PR #33, operational E2E PR #35, offline-first PR #36 | session/order/payment/EOD, outlet-specific accounts, offline replay, duplicate prevention, returns, stock and GL |
| HR / People / Payroll | Not sufficiently established by surfaced PR evidence | inventory files/routes/models; employee lifecycle, attendance, leave, payroll, statutory configuration and GL |
| Biometric attendance | No provider/device implementation verified from surfaced evidence | inspect device adapters, event ingestion, device registry, clock drift, offline sync, dedupe, employee mapping, privacy and exception workflow |
| CRM / Marketing | Included in the global gap review scope | lead/contact/opportunity lifecycle, consent, campaign queue, conversion to sales and reporting |
| SaaS / Tenants / Plans | PR #37 describes plan catalog and entitlement synchronization | tenant isolation, subscription lifecycle, module/limit enforcement on backend, billing events and race conditions |
| Salla / Shipping | PRs #17, #28, #31, #32 describe public-app foundation and shipping-state fixes | OAuth/webhook signature, replay protection, token refresh, state transitions, retry/dead-letter queue and reconciliation |
| AI reporting | PR #22 indicates reporting automation surface | permissions on source data, explainability/source links, prompt/data isolation, accuracy tests and provider failure behavior |
| Documents / Approvals / Audit | PR #25 mentions legal content and authorization; PR #18 calls out universal workflow/audit gaps | document versioning, approval matrix, signature integration, retention, exports, tamper-evident audit and backend-only authorization |
| Projects / Hospitality / Leasing / Fleet / Manufacturing / WMS | Included in architecture/gap-audit scope; exact current completeness not verified | establish route-to-model coverage, workflows, permissions, tests and cross-module links separately |

## Known audit signals that must be resolved
- The global gap audit (PR #18) specifically prioritizes end-to-end transaction integrity, accounting/reconciliation depth, WMS/costing, frontend completion, universal workflow/audit, BI and integration reliability.
- PR #29 explicitly leaves Treasury GL posting, cross-module tenant-boundary proof and partial-fulfillment semantics open at that stage.
- PR #30 introduces Treasury-to-Accounting integration and requires release-gate verification.
- PR #33 intentionally defers partial reservation ledger semantics and payment-method-specific GL mapping; PR #35/PR #36 add subsequent POS hardening, so the final branch must be checked to establish which gaps remain.
- PR #17 notes that Salla Partner Portal setup is external to the repository; credentials/scopes/webhook configuration cannot be proven by code alone.

## Repository verification commands for CI / a future local run
1. Confirm the exact branch, commit, and base before making changes.
2. Enumerate frontend routes/navigation and backend routers/controllers/services.
3. Map every route to authorization, persistence models, migration(s), tests and UI actions.
4. Inspect every migration graph and require a single deterministic head.
5. Run backend unit/integration tests and frontend lint/typecheck/build.
6. Run clean PostgreSQL migration tests and seed only synthetic test data.
7. Run cross-tenant authorization negative tests.
8. Run E2E journeys from the full-system plan, asserting both document status and resulting ledger/inventory balances.
9. Produce machine-readable module inventory and attach test results to the pull request.
10. When hardware is available, separately test biometric devices, printers, bank/payment providers and other real external systems.

## Exit criteria
A module is not "complete" until the main happy path, failure/retry path, permissions, audit trail, idempotency, database constraints, UI/API consistency and downstream accounting/reporting effects have tests. Configuration-dependent integrations must be labeled CONFIGURATION_REQUIRED until verified in a provider sandbox or real test device.
