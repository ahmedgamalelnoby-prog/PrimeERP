# Company Policy Settings — Static Wiring Audit

Date: 2026-10-22  
Branch: `feature/primeerp-full-system-audit-20261020-v2`

## Result

- Catalog entries audited individually: **71**.
- Current registry classification: **66 runtime / 5 catalog-only**.
- This is a source-level classification, not proof that migrations, tests, or end-to-end workflows have passed. The catalog-only list below reflects the current registry; runtime claims still require CI and workflow verification.
- Confirmed runtime consumers: `inventory.allow_negative_stock` (stock-movement posting), `inventory.allow_below_cost_sale` (delivery posting compares net line revenue with outbound stock valuation and requires the dedicated permission plus an audit event), `accounting.require_journal_approval` (journal posting), `general.timezone`, `general.base_currency`, `general.allow_multi_currency`, `general.require_cost_center`, `general.require_project`, `sales.document_numbering` (atomic company/year, company, or global numbering sequences), `hr.leave_requires_approval` / `hr.allow_negative_leave_balance` (leave request decisions and paid-leave balance checks), `hr.require_attendance_approval` (attendance correction decisions), `hr.default_work_hours_per_day` / `hr.overtime_requires_approval` (overtime eligibility and approval), and `accounting.allow_backdated_entries` (journal/generic transaction creation), plus `integrations.retry_limit` and `integrations.webhook_signature_required` (integration retry and Salla webhook intake), `accounting.fiscal_year_start_month` (fiscal-year creation), `accounting.rounding_method` and `tax.default_tax_inclusive_pricing` (tax calculation), `workflow.allow_self_approval` (generic transaction approval and HR leave/attendance decisions), `inventory.require_bin_location` (stock movement creation), `inventory.auto_reserve_sales_orders` (sales-order confirmation reservations, partial delivery consumption, and cancellation release), `general.branch_required` (generic transaction creation), and `accounting.period_lock_enabled` (journal posting), `sales.credit_limit_enforced` (customer credit exposure check), `purchasing.require_goods_receipt` (supplier-bill creation), `sales.default_payment_terms_days` / `purchasing.default_payment_terms_days` (sales invoices and supplier bills when partner terms are unset), `crm.duplicate_customer_check` (customer creation by email/tax number), `pos.allow_discount_without_approval` / `pos.max_discount_pct_without_approval` (POS checkout discounts), `inventory.require_warehouse` (stockable/consumable commerce documents), `inventory.expiry_tracking_required`, `inventory.serial_tracking_default`, and `inventory.batch_tracking_default` (new inventory-item defaults consumed by item creation; serial/expiry imply batch tracking), `notifications.email_enabled`, `notifications.whatsapp_enabled`, and `notifications.retry_limit` (company-scoped delivery gates and bounded transient retries), `tax.require_tax_code_on_invoice` (taxable sales/purchase invoice lines), and `accounting.auto_post_sales_invoice` / `accounting.auto_post_purchase_invoice` (company-gated accounting auto-post), and the five `accounting.default_*_account` code settings (company-scoped active posting-account overrides for commerce AR, AP, sales, purchase expense, and payment/cash lines), and `purchasing.allow_invoice_price_variance` / `purchasing.price_variance_tolerance_pct` (supplier bill vs linked receipt valuation comparison at bill accounting posting), `purchasing.require_purchase_order` (bills must reference a confirmed company/vendor purchase order and line-matched receipts), `sales.require_quote_approval` / `sales.require_order_approval` / `purchasing.require_purchase_approval` (orders pause in pending approval, enforce requester separation and require an authorized separate decision before confirmation), `general.intercompany_enabled` (new intercompany transaction creation), and `tax.einvoice_required_for_sales` (sales invoices and credit notes require ETA status `valid` before confirmation), and `inventory.valuation_method` (default costing method for newly created items when no item-specific choice is submitted), and `sales.allow_negative_customer_balance` (explicitly permits overpayment of a sales invoice to create customer credit), and `sales.invoice_requires_delivery` / `sales.allow_overbilling` (order-linked stock invoice quantities are checked against posted delivery quantities and ordered quantities), plus `integrations.auto_sync_enabled` (the scheduled Salla integration worker checks the company policy before claiming due connections; manual sync remains available). FIFO negative issues remain blocked for valuation safety, and reserved quantities remain protected.
- This is a source-level audit, not a successful runtime test. The GitHub Windows self-hosted Release Gate is currently queued; no test-pass claim is made until the run completes on the latest commit.

## Status definitions

- **RUNTIME**: code path found that reads this setting and changes/enforces workflow behavior, with documented guardrails.
- **CATALOG ONLY**: UI, API, storage and type validation exist, but no workflow consumer was verified. It must not be treated as active business logic.

## General (9)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `general.default_language` | enum | **RUNTIME** | Applies the saved company interface language when the Company Policy Settings page loads or saves |
| `general.date_format` | enum | CATALOG ONLY | Date display format |
| `general.timezone` | string | **RUNTIME** | Company-local date used by journal backdating policy |
| `general.base_currency` | string | **RUNTIME** | Default journal currency and foreign-currency policy |
| `general.allow_multi_currency` | bool | **RUNTIME** | Allow foreign-currency journal entries |
| `general.require_cost_center` | bool | **RUNTIME** | Require cost center on every journal line |
| `general.require_project` | bool | **RUNTIME** | Require a same-company project on generic business transactions |
| `general.branch_required` | bool | **RUNTIME** | Reject generic transaction creation without a branch when enabled |
| `general.intercompany_enabled` | bool | **RUNTIME** | Block creation of intercompany transactions while disabled |

## Accounting (12)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `accounting.period_lock_enabled` | bool | **RUNTIME** | Enforce period status/allow-posting checks when posting journals |
| `accounting.allow_backdated_entries` | bool | **RUNTIME** | Allow journal dates before company-local today, subject to period controls |
| `accounting.require_journal_approval` | bool | **RUNTIME** | Require approval before journal posting |
| `accounting.auto_post_sales_invoice` | bool | **RUNTIME** | Gate automatic posting of sales-invoice journals, alongside accounting/journal configuration |
| `accounting.auto_post_purchase_invoice` | bool | **RUNTIME** | Gate automatic posting of purchase-bill journals, alongside accounting/journal configuration |
| `accounting.rounding_method` | enum | **RUNTIME** | Tax calculation rounding mode |
| `accounting.fiscal_year_start_month` | int | **RUNTIME** | Enforce configured month when creating a fiscal year |
| `accounting.default_receivable_account` | string | **RUNTIME** | Overrides the commerce receivable account using an active company posting-account code; blank preserves legacy configuration |
| `accounting.default_payable_account` | string | **RUNTIME** | Overrides the commerce payable account using an active company posting-account code; blank preserves legacy configuration |
| `accounting.default_sales_account` | string | **RUNTIME** | Overrides the commerce sales account using an active company posting-account code; blank preserves legacy configuration |
| `accounting.default_purchase_account` | string | **RUNTIME** | Overrides the commerce purchase-expense account using an active company posting-account code; blank preserves legacy configuration |
| `accounting.default_cash_account` | string | **RUNTIME** | Overrides the commerce payment account using an active company posting-account code; blank preserves legacy configuration |

## Taxes (3)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `tax.default_tax_inclusive_pricing` | bool | **RUNTIME** | Default tax-inclusive behavior when caller does not explicitly choose |
| `tax.require_tax_code_on_invoice` | bool | **RUNTIME** | Require tax codes when an invoice line has configured item taxes |
| `tax.einvoice_required_for_sales` | bool | **RUNTIME** | Require ETA status `valid` for the linked sales invoice/credit note before confirmation |

## Sales (8)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `sales.require_quote_approval` | bool | **RUNTIME** | Pause quotation confirmation for a separate approval decision when enabled |
| `sales.require_order_approval` | bool | **RUNTIME** | Pause order confirmation for a separate approval decision when enabled |
| `sales.invoice_requires_delivery` | bool | **RUNTIME** | Require posted delivery for linked stock order lines before invoicing |
| `sales.allow_overbilling` | bool | **RUNTIME** | Allow order-linked invoices above ordered quantities |
| `sales.credit_limit_enforced` | bool | **RUNTIME** | Apply customer credit-limit checks when enabled |
| `sales.allow_negative_customer_balance` | bool | **RUNTIME** | Permit an invoice overpayment to create a customer credit balance |
| `sales.default_payment_terms_days` | int | **RUNTIME** | Default due-date terms for sales invoices when partner terms are unset |
| `sales.document_numbering` | enum | **RUNTIME** | Generate unique sales document numbers per company/year, per company, or globally |

## Purchasing (6)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `purchasing.require_purchase_order` | bool | **RUNTIME** | Require linked confirmed PO and matching receipt lines before supplier billing |
| `purchasing.require_purchase_approval` | bool | **RUNTIME** | Pause purchase-order confirmation for a separate approval decision when enabled |
| `purchasing.require_goods_receipt` | bool | **RUNTIME** | Block supplier-bill creation without a validated receipt link when enabled |
| `purchasing.allow_invoice_price_variance` | bool | **RUNTIME** | Allow linked receipt-vs-bill stock valuation variance above the configured tolerance |
| `purchasing.price_variance_tolerance_pct` | number | **RUNTIME** | Maximum invoice-vs-receipt stock valuation variance percentage before the allow-beyond-tolerance switch is required |
| `purchasing.default_payment_terms_days` | int | **RUNTIME** | Default due-date terms for supplier bills when partner terms are unset |

## Inventory (9)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `inventory.allow_negative_stock` | bool | **RUNTIME** | Allow stock to fall below zero where the valuation method supports it |
| `inventory.valuation_method` | enum | **RUNTIME** | Default for new inventory items when no item-level costing method was explicitly submitted; existing items do not change |
| `inventory.require_warehouse` | bool | **RUNTIME** | Require a warehouse for stockable/consumable commerce document lines |
| `inventory.require_bin_location` | bool | **RUNTIME** | Require child/bin locations for stock movement endpoints |
| `inventory.auto_reserve_sales_orders` | bool | **RUNTIME** | Reserve components at order confirmation, consume safely across partial deliveries, and release remaining reservations on cancellation |
| `inventory.allow_below_cost_sale` | bool | **RUNTIME** | Compare net delivery-line revenue with posted inventory issue cost; an override needs the dedicated permission and is audited |
| `inventory.expiry_tracking_required` | bool | **RUNTIME** | Default expiry tracking on new items; expiry/batch constraints are enforced by stock workflows |
| `inventory.serial_tracking_default` | bool | **RUNTIME** | Default serial tracking on new items; serial/batch traceability is supported by item/movement workflows |
| `inventory.batch_tracking_default` | bool | **RUNTIME** | Default batch tracking on new items; serial/expiry tracking also implies batch tracking |

## Human Resources (8)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `hr.attendance_source` | enum | CATALOG ONLY | Attendance source |
| `hr.require_attendance_approval` | bool | **RUNTIME** | Require a separate decision before attendance corrections are applied |
| `hr.overtime_requires_approval` | bool | **RUNTIME** | Require a separate decision for requests above the daily standard |
| `hr.leave_requires_approval` | bool | **RUNTIME** | Require a separate decision before a leave request is approved and its paid-leave balance consumed |
| `hr.payroll_requires_approval` | bool | CATALOG ONLY | Require payroll approval before posting |
| `hr.allow_negative_leave_balance` | bool | **RUNTIME** | Allow approved paid leave to exceed configured balance; unpaid leave does not consume a balance |
| `hr.default_work_hours_per_day` | number | **RUNTIME** | Subtract configured daily hours from recorded attendance when calculating eligible overtime |
| `hr.biometric_sync_interval_minutes` | int | CATALOG ONLY | Target sync interval for biometric integrations |

## Approvals (3)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `workflow.approval_mode` | enum | CATALOG ONLY | Approval chain mode |
| `workflow.allow_self_approval` | bool | **RUNTIME** | Block requesters from approving their own generic transactions when disabled |
| `workflow.escalation_after_hours` | int | CATALOG ONLY | Escalate pending approvals after hours |

## Point of Sale (4)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `pos.allow_open_cash_drawer` | bool | CATALOG ONLY | Allow cash drawer opening without a transaction |
| `pos.require_shift_close` | bool | **RUNTIME** | Require an open terminal shift before checkout and save expected cash, counted cash, and variance when the cashier closes the shift |
| `pos.allow_discount_without_approval` | bool | **RUNTIME** | Permit discounts above the no-approval threshold when enabled |
| `pos.max_discount_pct_without_approval` | number | **RUNTIME** | Enforce maximum POS discount percentage when approval-free discounts are disabled |

## Manufacturing (2)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `manufacturing.require_work_order` | bool | **RUNTIME** | Require production stock movements to match a released work order in the same company |
| `manufacturing.allow_overproduction` | bool | **RUNTIME** | Block production above planned quantity when disabled; the completion service reads the company policy |

## CRM (1)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `crm.duplicate_customer_check` | bool | **RUNTIME** | Block active customer duplicates by matching normalized email or tax number when enabled |

## Integrations (3)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `integrations.auto_sync_enabled` | bool | **RUNTIME** | Scheduled Salla full-sync worker checks this company policy before claiming due connections; manual sync remains available |
| `integrations.retry_limit` | int | **RUNTIME** | Maximum manual integration event retries before dead-lettering |
| `integrations.webhook_signature_required` | bool | **RUNTIME** | Require signature for public Salla webhook intake; supplied signatures are always verified |

## Follow-up review fixes (2026-10-20)

- Corrected purchase-bill source idempotency lookup so it no longer passes an unsupported keyword to _existing_source.
- Applied accounting.auto_post_purchase_invoice at the actual purchase-bill posting decision, rather than during the existing-source lookup.
- Aligned commerce accounting-period selection with accounting.period_lock_enabled; the journal posting service remains the enforcement point and still checks company/fiscal-year membership and entry-date range.
- Hardened POS discount behavior: when approval-free discounts are disabled, any positive discount is rejected because the checkout path has no approval-capture workflow; when enabled, discounts above pos.max_discount_pct_without_approval are rejected.
- Aligned journal reversals with the company timezone, `accounting.allow_backdated_entries`, and `accounting.period_lock_enabled`; period lookup can select a date-covering period without open-status filtering when the company explicitly disables period locking. Tenant/company scope and period date coverage remain enforced.
- Added a focused regression test proving a backdated journal reversal is rejected before accounting-period lookup when `accounting.allow_backdated_entries` is disabled. This test is committed but has not yet run successfully.
- Added POS regression coverage for approval-required discounts, above-limit discounts, and an allowed discount at the configured limit. These tests are committed but have not been executed successfully.

## Defects and improvements made during this audit

1. Validation now rejects unknown setting keys, invalid enum values, wrong booleans, non-finite numbers (NaN/Infinity), invalid IANA time zones, malformed 3-letter uppercase currency codes, out-of-range fiscal year months, and workday lengths outside 0–24 hours.
2. Added parameterized tests for every catalog default, key validation boundaries, company rounding modes, and self-approval policy. These tests are committed but have **not yet been executed successfully** locally or in CI.
3. The UI distinguishes runtime-enabled settings from catalog-only settings, so saving a value does not falsely imply that a business workflow uses it.
4. Company settings writes are tenant-scoped, permission-protected, and audited by changed key names without recording values or credentials.

## Recommended order for remaining wiring

1. Continue HR foundations: biometric/mobile attendance ingestion, payroll approval/posting, and a workday/holiday calendar. Manual attendance, correction approval, and overtime eligibility/approval now have working API paths.
2. Inventory traceability: keep verifying batch, serial and expiry enforcement through receiving, transfers, sales delivery and returns. Automatic order reservation now reserves stock at confirmation, consumes reservations safely through partial deliveries, and releases remaining reservations on cancellation.
3. Approval engine: extend the commerce single-decision flow with configurable approver chains and a reliable escalation scheduler before enabling `workflow.approval_mode` or `workflow.escalation_after_hours`.
4. Integrations: automatic Salla sync now has a dedicated worker and company-policy gate; add provider-specific scheduling only when another provider is supported.
5. Broaden company date-format display across all relevant tables, forms, exports and reports before changing `general.date_format` from catalog-only.
6. Review the remaining inventory policy controls (below-cost authorization and cost-layer checks) after cost and permission checks are consistently exposed to the sales workflow.

The leave-request foundation now enforces company-scoped balances, overlapping-request checks, policy-controlled self-approval, approval/rejection audit events, and balance restoration when an approved leave is cancelled before its start date. Requested leave days are supplied by the authorized HR user and bounded by the inclusive calendar date span; a company workday/holiday calendar is not yet available. Attendance, overtime, payroll approval, POS shift, and scheduled integration foundations remain incomplete. A catalog entry must stay catalog-only until its owner workflow exists and is wired. This document is a source-level audit; migrations and tests were not executed in this environment.

A setting should be promoted from CATALOG ONLY to RUNTIME only after the consumer is wired, company-isolation tests pass, and positive/negative workflow tests prove the behavior.


## Settings UI organization update
- Company policies remain grouped by category in registry order. Within a category, runtime-enforced entries are listed before catalog-only entries, then labels are alphabetically sorted using Arabic locale rules.
- The page now searches by display label, canonical setting key, module, and translated category/module names; a status filter narrows results to runtime or catalog-only entries.
- The page shows total/runtime/catalog/unsaved-change counters, a result count, a reset control, an empty-result message, and disables Save when no values differ from the loaded values.
- These UX changes improve navigation. The current source audit records **57 runtime / 11 catalog-only** after wiring sales numbering, approval lifecycles, project dimensions, linked sales/purchase workflows, and POS cashier shifts. Migrations and tests have not been executed in this environment.


## Follow-up regression coverage (2026-10-20)
- Added focused unit coverage for the fiscal-period repository's two policy modes: default lookup filters to periods that are both open and allow posting; `require_open=False` retains tenant/company/date coverage filters while omitting those two state filters.
- This tests the repository contract used by `accounting.period_lock_enabled` without requiring Docker or a database service. It does not replace the full journal reversal integration test.
- Current CI status at time of update: the Windows self-hosted release gate for the preceding commit was queued and had not reported a result. The new commit may trigger another self-hosted run; no test-pass claim is made.


## Registry validation regression coverage (2026-10-20)
- Added isolated tests for malformed currency codes, invalid IANA timezones, out-of-range POS discount percentages, boolean type confusion, and unknown setting keys.
- Added a registry contract test checking key uniqueness and that every declared default passes its own type/range validator.
- These are source-level unit tests only; they have not been executed because the Windows self-hosted runner depends on the user's currently-offline machine. No green CI status is implied.


## Follow-up verification on 2026-10-20

- Corrected the registry test's expected runtime-setting set to match the 27 settings currently marked `runtime`; the test had retained an older 14-setting expectation and would fail despite the newer registry coverage.
- Added/retained validation coverage for invalid values and defaults in `backend/tests/test_company_policy_runtime.py` and `backend/tests/test_company_settings_registry.py`.
- These are source-level corrections only. The self-hosted Windows runner is still queued while the user's local machine is unavailable, so no test pass is claimed.

## Follow-up safety review — 2026-10-20

A second source review deliberately did **not** promote several settings to runtime, because the current data/workflow model cannot enforce them safely:

- `sales.require_order_approval` and `purchasing.require_purchase_approval`: commerce confirmation currently transitions a draft document directly to confirmed; no company-policy-aware approval state transition was verified for these document types.
- `sales.invoice_requires_delivery` and `sales.allow_overbilling`: sales documents do not carry a verified order-to-delivery/invoice line-allocation relationship that can prove which quantities have been delivered or billed. Matching only by customer would risk accepting an unrelated delivery or rejecting a valid invoice.
- `purchasing.require_purchase_order`: purchase bills do not carry a verified purchase-order source relationship; matching only by vendor is insufficient.
- `integrations.auto_sync_enabled`: a dedicated integration worker now polls active Salla connections, applies the company-level enablement gate and configured polling interval, claims one connection before network I/O, and leaves manual sync independently callable. Verify worker deployment and end-to-end retries in CI before treating operational availability as proven.
- `general.require_project`: commerce document schemas/models reviewed here do not expose a project dimension to validate.

A registry regression test now asserts these options remain `catalog` until the corresponding safe workflow/data model exists. This is intentional: a visible toggle is not proof of enforcement. The next implementation batch should add the missing source relationships/approval states or scheduler first, then wire and test the relevant setting end-to-end.

Tests remain **not executed/verified** in this review; the local Windows self-hosted runner is unavailable, and no paid hosted runner was used.

### Focused runtime regression tests added — 2026-10-20

Added `backend/tests/commerce/test_company_auto_post_policy.py` to exercise the actual accounting service posting path with isolated dependencies: when `accounting.auto_post_sales_invoice` is false, the journal is submitted but not posted automatically; when true, auto-post proceeds (assuming the existing company accounting configuration and journal also allow it). These tests are committed but have **not been executed** because the permitted self-hosted runner remains unavailable.


### Purchase auto-post regression coverage (2026-10-20)

The focused commerce accounting tests now exercise both company gates at the journal-posting decision:
- `accounting.auto_post_sales_invoice`: enabled and disabled cases.
- `accounting.auto_post_purchase_invoice`: enabled and disabled cases.

Each disabled case expects the draft journal to be submitted but not posted automatically; each enabled case expects the post transition, provided the existing commerce and journal auto-post switches also permit it. These are committed tests, not evidence of a passing run. Verification still depends on the local Windows self-hosted runner becoming available; no paid hosted runner was added.


### Integration retry-limit regression coverage (2026-10-20)

Added focused tests for `integrations.retry_limit`: an event at the configured attempt limit is moved to `dead_letter` and returns HTTP 409, while an event below the limit is allowed through the retry/process path. These tests are committed but not yet verified by execution. The free-only constraint remains in force; the self-hosted Windows release gate is still the only configured test gate.


### Salla webhook signature verification regression coverage (2026-10-20)

Added focused unit tests for the Salla signature verifier: a valid HMAC-SHA256 signature is accepted, an invalid signature is rejected with HTTP 401, and a missing signature is rejected with HTTP 401. These exercise the verifier itself; they do not replace a full endpoint test of the company-level `integrations.webhook_signature_required` switch. Tests remain unverified until the self-hosted Windows runner executes them.


### Salla webhook company-policy endpoint coverage (2026-10-20)

Added a public-webhook endpoint regression test that sets `integrations.webhook_signature_required` to true and verifies a request with no signature is rejected with HTTP 401 before JSON/event processing. This complements the direct valid/invalid HMAC verifier tests. The endpoint test is committed but has not been executed; the self-hosted Windows runner remains the only permitted test gate, and no passing result is claimed.


## Remaining catalog-only backlog — grouped implementation plan (2026-10-20)

The catalog-only settings below are the remaining candidates for workflow wiring. This historical plan may contain completed items; use the updated review section below as the current status. Grouping is by the primary workflow needed; it is not a claim that the work is already implemented.

### A. Company defaults and accounting configuration (1)
- `general.date_format`: apply the selected format consistently through shared frontend date-formatting utilities; display-wide wiring is still incomplete.

### B. Sales and customer rules (1)
- `sales.document_numbering`: keep catalog-only until sales has its own transaction-safe numbering sequence and migration. Current `DocumentCreate.number` is caller-required; the generic sequence requires a branch and is scoped by tenant/company/branch, while this policy also offers global numbering. Existing uniqueness is only `(company_id, document_type, number)`, so reusing that sequence would not faithfully enforce all three choices.

### D. Inventory and costing (5)
- `inventory.auto_reserve_sales_orders` is now runtime: order confirmation reserves per-line recipe components, deliveries consume reservations partially, and order cancellation releases the remaining reservation.
- `inventory.allow_below_cost_sale`: enforce using current valuation cost and explicit permission/audit behavior at sales-line validation.
- `inventory.expiry_tracking_required`, `inventory.serial_tracking_default`, `inventory.batch_tracking_default`: connect item tracking flags to receipt, stock movement, lot/serial identity and issue validation; defaults should affect new items only unless a migration is deliberately approved.

### E. HR (8)
- `hr.attendance_source`, `hr.biometric_sync_interval_minutes`: add supported source adapters and a scheduler/worker with per-company configuration.
- `hr.require_attendance_approval`, `hr.overtime_requires_approval`, `hr.leave_requires_approval`, `hr.payroll_requires_approval`: implement approval states and role checks in each corresponding HR lifecycle before marking runtime.
- `hr.allow_negative_leave_balance`: enforce at leave request/approval and concurrent balance update.
- `hr.default_work_hours_per_day`: use as a company fallback in schedules and overtime calculations where an employee-specific schedule is absent.

### F. Approval engine and operations (2)
- `workflow.approval_mode`, `workflow.escalation_after_hours`: complete the approval engine (sequential/parallel/any-one decisions, due-time tracking, escalation jobs and audit trail). Do not wire these to UI labels alone.

### G. POS and manufacturing (4)
- `pos.allow_open_cash_drawer`, `pos.require_shift_close`: add permission-checked cash-drawer events and enforced shift close/reconciliation before session finalization.
- `manufacturing.require_work_order`, `manufacturing.allow_overproduction`: enforce work-order linkage and planned-vs-produced quantity at production completion, with stock/ledger consistency.

### H. Integrations (1)


### Recommended execution sequence
1. Low-dependency defaults: date/language presentation, account-code fallback resolution, workday/payment defaults where their owning service already exists.
2. Finish the remaining sales quotation threshold and numbering policies; complete approval-chain/escalation support before promoting generic approval-mode settings.
3. Inventory tracking/reservation/costing after migrations and valuation compatibility review.
4. HR and approval engine with schedulers/workers and auditable transitions.
5. POS session lifecycle, manufacturing completion controls, intercompany, and scheduled integration sync.

For each policy, promotion to `runtime` requires: (a) an identified authoritative workflow boundary, (b) company/tenant isolation, (c) positive and negative tests, and (d) successful execution in the free self-hosted test gate. Until then it remains explicitly `catalog`.


## Company language preference wiring (2026-10-20)

- Promoted `general.default_language` to runtime because authenticated app bootstrap now loads the selected active company's saved `ar`/`en` language through the existing i18next instance; the Company Policy Settings page also applies it when settings are loaded and after settings are saved. The existing i18n handler updates document language/direction and persists the selected language locally.
- Bootstrap uses the saved `company_id` when it matches an active company, otherwise it selects the first active company and stores that selection. If company lookup/settings cannot load, bootstrap leaves the current browser/user language unchanged rather than blocking authentication.
- Updated the registry contract test to include this key among verified runtime consumers. Tests remain unexecuted in this environment; no green status is claimed.


## Additional catalog validation coverage (2026-10-20)

- Added registry tests confirming that only the three declared `general.date_format` values are accepted.
- Added boundary tests for `purchasing.price_variance_tolerance_pct` including negative, above-100, non-finite and wrong-type inputs. These settings remain catalog-only until their full display/workflow consumers are implemented.
- These are committed regression tests; execution is still pending on the offline self-hosted runner and is not claimed as passing.


## Additional accounting default-account wiring (2026-10-20)

The five company account-code settings are now consumed by `CommerceAccountingService`. A non-empty configured code must resolve to an active `AccountCombination` belonging to the same company and an active, posting `NaturalAccount` belonging to that company. Unknown, inactive, non-posting, or cross-company codes fail closed with HTTP 409. Empty values retain the existing `CommerceAccountingSettings` account IDs for backward compatibility. The mappings cover receivable, payable, sales, purchase-expense, and payment/cash lines in commerce accounting flows. A configured code overrides the existing commerce account ID; a blank setting preserves that legacy ID. They do not replace inventory, GRNI, tax, COGS, WHT, or purchase-price-variance accounts.

Regression tests cover a configured override, an unset fallback, and invalid-code rejection. These tests are committed but have not been executed in this environment; the self-hosted runner status remains the gate for verification.


## Partial company date-format display support (2026-10-20)

- Added a pure formatter for the three declared date formats and connected it to the generic commerce operational list. That page loads `general.date_format` for the selected company and formats ISO date-only fields without timezone conversion; if the settings API fails or returns an unsupported value, the page falls back to `DD/MM/YYYY` and remains usable.
- This is deliberately **not** promoted to runtime: other pages and date-bearing workflows have not yet been audited and migrated to the shared formatter. The setting remains catalog-only until date formatting is consistent across the application.
- Frontend build/tests have not been executed in this environment.


## Purchase price variance policy wiring (2026-10-20)

- Promoted `purchasing.allow_invoice_price_variance` and `purchasing.price_variance_tolerance_pct` to runtime.
- At supplier-bill accounting posting, when the bill is linked to received goods, the service compares the bill's stock-item subtotal with the allocated receipt valuation. A variance within the configured percentage is accepted; a variance above tolerance returns HTTP 409 unless the company explicitly enables `purchasing.allow_invoice_price_variance`.
- This implementation currently evaluates the aggregate stock-item valuation variance against linked receipts, not a per-line PO comparison. Purchase-order relationships and purchase-approval lifecycle remain unimplemented and catalog-only.
- Added focused tests for equal values, at-tolerance and above-tolerance values, the explicit allow-beyond-tolerance switch, and downward variance. Tests are committed but not yet executed; the self-hosted release gate remains queued, so no passing result is claimed.
- The generic commerce list's date formatter was also hardened to preserve an ISO timestamp suffix and leave invalid ISO-like dates unchanged; the date-format setting remains catalog-only until app-wide display coverage is complete.


## Effective account-default isolation fix (2026-10-20)

- The commerce accounting service now builds a detached effective-settings value object before applying company account-code overrides. It no longer mutates the SQLAlchemy `CommerceAccountingSettings` row while resolving runtime policy values, preventing a later unrelated transaction commit from persisting an override into the legacy account-ID columns.
- Added a regression test that checks effective account IDs use the company policy values while the persisted legacy values remain unchanged.
- This is source-level verification only; the test has not run because the configured free self-hosted Windows runner is unavailable. No passing test status is claimed.


## Company date-format preference synchronization (2026-10-22)

- Added a company-scoped browser preference helper for the validated `general.date_format` values. Authenticated bootstrap hydrates it from the selected company's settings, and the Company Policy Settings page refreshes it when a company is loaded or saved.
- The commerce operational list continues to read the authoritative setting from the API and keeps the company-scoped preference cache in sync. A reactive shared hook applies the cached preference to dashboard date, commerce operational lists, journal entries, AR aging, fiscal-year/period dates, partner statements, user last-login dates, bank reconciliation dates, treasury cheque due dates, and shipment/settlement dates.
- This still does not make date display consistent across every module: several other screens and exports have not been migrated to the shared formatter. `general.date_format` correctly remains catalog-only until that migration is complete.
- No frontend build or tests were run in this environment.


## Newly connected company policy consumers (2026-10-22)

- `general.intercompany_enabled` now gates creation of intercompany transactions in the enterprise finance API. Queries and consolidation workflows remain available for existing records; this switch controls creation of new intercompany entries.
- `tax.einvoice_required_for_sales` now requires a linked Egyptian e-invoice with ETA status `valid` before a sales invoice or credit note can be confirmed. The draft commerce document must first be registered with ETA and reach valid status; missing, queued, submitted, rejected, or errored ETA documents block confirmation.
- Both settings are marked runtime and included in the registry contract's expected consumer set. Tests have not been executed in this environment.


- `inventory.valuation_method` is now the default costing method for new items only when the request did not explicitly provide an item-specific method. Existing item costing is not rewritten; the per-item accounting valuation continues to use each item's stored method.


- `sales.allow_negative_customer_balance` now permits a customer payment to exceed the outstanding total on a sales invoice when enabled, recording the excess as customer credit. The default false setting continues to reject overpayment, and purchase/vendor payments remain subject to the outstanding-balance limit.


## Sales document numbering workflow (2026-10-22)

- Added an atomic sequence table and allocator for sales quotations, orders, deliveries, invoices, and credit notes. Supported scopes are per company and fiscal/calendar document year, per company, or global; the default is per company/year.
- Sales numbers are generated by the backend, and any caller-supplied sales number is ignored. The sales UI now explains the generated numbering; purchase document numbers remain required from the purchasing workflow.
- The registry and its expected runtime contract now mark `sales.document_numbering` as runtime. Migration and tests have not been executed in this environment; this is a source-level wiring review, not a runtime-pass claim.

## Sales order delivery/invoice quantity controls (2026-10-22)

- Added a nullable source-order reference on sales delivery/invoice documents and a nullable source-order-line reference on each linked sales line, with same-company/customer/order validation and a migration adding foreign keys and lookup indexes.
- Creating an order-linked delivery or invoice now locks the source order, requires the order to be confirmed, validates item/variant identity, and aggregates existing linked quantities under that lock.
- With `sales.invoice_requires_delivery` enabled, stockable/consumable invoice lines must link to an order and cannot exceed its posted (fulfilled/posted) delivery quantity less quantities already invoiced. Non-stock lines are not forced through delivery.
- With `sales.allow_overbilling` disabled, an order-linked invoice cannot exceed the source order line quantity. Enabling it removes only this ordered-quantity ceiling; the delivery policy still applies independently when enabled. Standalone invoices with no source order remain valid because they are not order overbilling.
- Both policies are now marked runtime. Registry contract expectations were updated; tests and migrations were not executed here, so the feature is not claimed as runtime-verified yet.


## Purchase order to receipt/bill links (2026-10-22)

- Added source-order references to purchase receipt/bill headers and source-purchase-line references to their lines, with company/vendor/type/status/item/variant validation and dedicated foreign keys/indexes.
- With `purchasing.require_purchase_order` enabled, a new supplier bill must identify a confirmed purchase order and every bill line must map to a line on that order. When the bill cites goods receipts, each cited receipt must also be linked to that same order. The existing goods-receipt policy continues to require received receipt IDs independently.
- The policy is now runtime. The registry contract was updated, but migrations and tests have not been executed here; no runtime-pass claim is made.


## HR leave balance and approval workflow (2026-10-22)

- Added company-scoped leave balances by employee and leave type, plus leave requests with pending, approved, rejected, and cancelled states. Requests validate active employee/company ownership, date order, requested days against the inclusive calendar span, and overlapping pending/approved periods.
- `hr.leave_requires_approval` pauses requests for a separate `enterprise.post` decision. When disabled, the request is automatically approved and the paid-leave balance is consumed in the same transaction. The requester cannot decide their own pending request unless `workflow.allow_self_approval` is enabled.
- `hr.allow_negative_leave_balance` controls whether annual, sick, and other paid leave can exceed the configured balance. Unpaid leave does not consume a balance. Cancelling a pending request is allowed for its requester; cancelling an approved request restores balance only before its start date in company timezone.
- The API records audit events for submission, decision, and cancellation without copying the private leave reason into audit metadata. Tenant/company checks are applied to every endpoint.
- Added the HR leave migration and model registration. The registry and contract now mark both settings runtime. Migration and tests have not been executed here.
- Leave days are currently entered by the authorized HR user because a company workday/holiday calendar has not been established; the API ensures entered days do not exceed the inclusive date span.

## HR attendance and correction workflow (2026-10-22)

- Added one company-scoped attendance record per employee/day, including company-timezone check-in/check-out validation and duplicate-day protection.
- Attendance entry accepts manual source only while `hr.attendance_source` is set to `manual`. Biometric, mobile, and integration values remain catalog-only because their authenticated ingestion connectors do not exist yet.
- Corrections retain the proposed values and reason. With `hr.require_attendance_approval` enabled, the record changes only after an authorized user approves, subject to `workflow.allow_self_approval`; when disabled, corrections apply immediately and are marked as policy-applied.
- The HR screen displays attendance in the company timezone and provides record, correction, and decision controls. Corrections and decisions are audit-logged without copying correction reasons into audit metadata.
- Added attendance/correction tables and a migration. The registry contract includes the runtime setting; migration and tests have not been executed.

## HR overtime request and approval workflow (2026-10-22)

- Overtime requests must reference a company-owned attendance record with check-in and check-out timestamps. Eligible hours are computed as recorded duration less `hr.default_work_hours_per_day`, rounded to two decimal places.
- Pending and approved requests reserve capacity against that attendance record. Concurrent requests lock the attendance row; decisions recheck the capacity before approval. Attendance corrections cannot reduce recorded hours below already requested or approved overtime.
- `hr.overtime_requires_approval` sends requests to a separate decision; when disabled, valid requests are auto-approved. `workflow.allow_self_approval` controls whether the requester may decide their own pending request.
- The HR page exposes request and decision actions. Audit events record status and hours without storing the private request reason in audit metadata.
- Added the overtime table and migration; registry contract now marks both overtime settings runtime. Migration and tests have not been executed.
- This records approved overtime, but payroll remains a draft preview and does not yet consume approved overtime or post a journal.


## Sales/purchase order approval lifecycle (2026-10-22)

- Sales quotations and sales/purchase orders configured to require approval now enter `pending_approval` on their first confirmation request, with a company-scoped actor/time/reason event. A user with the existing commerce posting permission can approve or reject; the decision is locked, stored in the audit timeline, and exposed through company-scoped approval-event endpoints. An approved order must be confirmed again to enter the existing operational status.
- `workflow.allow_self_approval` is enforced against the user who submitted the order for approval. Rejected documents remain rejected and require a replacement document; the current commerce module has no edit/resubmit endpoint.
- `sales.require_quote_approval`, `sales.require_order_approval`, and `purchasing.require_purchase_approval` are now runtime. Quotation approval applies to every quotation when enabled; no threshold setting currently exists. This is a single-decision lifecycle. `workflow.approval_mode` and `workflow.escalation_after_hours` remain catalog-only until approver-chain assignments and a reliable escalation scheduler are built.
- The approval-event table and status constraints have a migration. The exact registry contract was updated. Tests/migrations have not been executed; no pass is claimed.


## Project dimension on generic business transactions (2026-10-22)

- Added a nullable project foreign key to generic business transactions and an optional project ID to create/update/response schemas. The transaction service validates that a supplied project belongs to the transaction company; when `general.require_project` is enabled it also rejects creates and updates that leave the transaction without a project.
- Added the project-dimension migration and promoted `general.require_project` to runtime for the generic transaction engine. This does not claim project support on commerce documents or accounting journal lines that do not expose the dimension.
- Registry contract updated. Migration/tests have not been executed, so this is not runtime-verified.



## Remaining catalog-only review — updated 2026-10-22

Five policies remain catalog-only because their full owning workflows are not yet implemented or verified. The generic approval-request workflow now consumes `workflow.approval_mode`, and a polling worker now consumes `workflow.escalation_after_hours`; the latter queues idempotent in-app reminders for assigned pending approvers.

- `general.date_format`: a shared formatter and backend preference endpoint exist, but date-bearing screens, reports, and exports are not yet consistently migrated. Finish the app-wide display/export migration before promotion.
- `hr.attendance_source` and `hr.biometric_sync_interval_minutes`: manual attendance is enforced, but biometric/mobile ingestion still lacks an authenticated device connector and a scheduled sync worker for that source.
- `hr.payroll_requires_approval`: payroll remains a preview without a complete approval and journal-posting lifecycle.
- `pos.allow_open_cash_drawer`: cashier shifts reconcile cash sales, but authenticated drawer events and hardware-command integration are absent.

Do not promote these five settings until their owning workflows, tenant/company isolation, and tests are in place. Inventory tracking defaults remain runtime because item creation consumes the settings and the stock-movement lifecycle persists and validates lot/serial/expiry allocations. Source-level implementation is not a substitute for passing CI and migration/runtime validation. The escalation worker's deployment and delivery behavior also remain unverified until Docker/CI runs succeed.

## POS cashier shift foundation — 2026-10-22
- Added company/branch/terminal-scoped cashier shifts with one open shift per terminal, opening float, opener/closer, and close reconciliation fields.
- POS checkout now requires an active terminal shift while `pos.require_shift_close` is enabled and links each POS invoice to the shift. The offline POS page prevents closing while locally queued checkouts remain.
- Shift close calculates expected cash from the opening float plus posted cash payments linked to that shift, then records counted cash and variance. Card, bank, and wallet tenders remain outside the cash drawer total.
- The migration is committed but has not been executed. No tests or frontend build were run, so this remains a source-level implementation review.
- `pos.allow_open_cash_drawer` remains catalog-only: there is no authenticated cash-drawer hardware integration or drawer event workflow to enforce it.
- `manufacturing.require_work_order` is now runtime: production issue/receipt movements are checked against a released work order in the same company; material item/source location and output item/variant/destination must match the referenced work order.


## Manufacturing work-order workflow — 2026-10-22

- Added company-scoped work orders that snapshot the active recipe version and component rates, validate the recipe output, component items, and physical stock locations, and enforce unique work-order numbers per company.
- Work orders move through planned, released, completed, or cancelled states. Completion consumes the recipe-scaled components using inventory valuation, posts the component cost to the production clearing account, receives finished goods at the same total cost, and applies `manufacturing.allow_overproduction`. Direct material issues are blocked by default while `manufacturing.require_work_order` is enabled.
- Cancellation reverses the output receipt first and then the component issues. The inventory service blocks direct reversals of production movements so work-order state and WIP accounting cannot be bypassed.
- The manufacturing page now exposes work-order creation, release, completion, and cancellation. Components with active variants are rejected until recipe lines carry a component variant. Production costing also fails closed if the consumed value cannot be represented exactly at the current four-decimal inventory cost precision.
- Both policies are promoted to runtime and added to the registry contract. The migration and application verification have not been run in this environment; this is a source-level review only.


## Sales order stock reservation workflow — 2026-10-22

- When `inventory.auto_reserve_sales_orders` is enabled, confirming a sales order reserves its stock components across active physical locations in the order warehouse. Recipe expansion, variant, bin-location policy, and available stock are checked while locking location and warehouse balances.
- Linked partial deliveries consume the order-line reservation in the same transaction as each inventory issue. Partial consumption splits the consumed quantity from the still-active reservation, so subsequent deliveries retain the remaining reserved balance. The saved component reservations are the source of truth during delivery; later recipe edits do not change the confirmed order's material requirements.
- Cancelling an eligible sales order releases its remaining active reservations. Delivery posting rejects documents whose source order was cancelled. The sales screen exposes the warehouse on sales orders, copies it to linked deliveries, and offers order cancellation with a confirmation prompt.
- Orders created before the policy is enabled can reserve the quantity needed by a linked delivery at posting time. If the policy is disabled after reservations exist, linked deliveries still consume those reservations.
- The policy is promoted to runtime and included in the registry contract. No database schema change was needed because the existing reservation model supports source links and the existing stock move supports reservation IDs. No test suite or application build was run; this remains a source-level review.


## Below-cost sales control — 2026-10-22
- Promoted `inventory.allow_below_cost_sale` to runtime. Delivery posting compares each line's net revenue after discount and before tax against the actual posted outbound inventory moves (which carry the inventory valuation cost).
- Below-cost deliveries are blocked by default. When the company enables the policy, posting still requires the active `commerce.below_cost_override` role permission; the override records delivery, revenue, cost, and loss in the audit log in the same transaction.
- Added an idempotent migration that makes `commerce.below_cost_override` available in Roles & Permissions. A platform administrator still needs to assign it to authorized roles. The migration has not been executed, and no tests or builds were run; this remains a source-level review.

## Inventory lot/serial/expiry tracking — implementation expanded 2026-10-22
- Added per-item batch, serial, and expiry tracking flags. New-item defaults read the company policies; serial and expiry tracking imply batch tracking. Item update validation rejects explicit null values for these non-null flags.
- Added lot/serial/expiry fields to stock movement contracts, plus a location-level lot balance table with an expression-based unique identity across company, item, location, variant, lot, and serial.
- Posting now updates exact lot balances as part of the same database transaction as item/location/warehouse balances. Tracked movements are rejected if the requested lot has insufficient source quantity or the lot expiry identity conflicts.
- Outbound batch movements without an explicit lot use FEFO allocation: earliest non-expired expiry first, null-expiry lots last when expiry tracking is not mandatory, and no expired lots. Per-lot quantities are persisted in `inventory_lot_move_allocations` for audit. Serial-tracked movements must still identify one serial and have quantity exactly one.
- Reversal now applies the recorded per-lot allocation in reverse and blocks tracked reversals when the allocation audit is missing, rather than silently corrupting lot balances.
- Migrations added: `20261102_inventory_lot_balances` and `20261103_inventory_lot_move_allocations`, following `20261101_inventory_lot_serial_expiry`.
- Verification status: source and contract tests have been updated, but GitHub Actions is still pending/running at the time of this note. Do not mark this workflow production-verified until the latest run passes and the migrations are applied successfully in the target database.

## Required work-order policy enforcement — 2026-10-22

- Enabled the `manufacturing.require_work_order` runtime consumer at inventory stock-movement creation for production issues and production receipts.
- When enabled, a production issue must reference an existing material line belonging to a released work order in the same company; item and source location are checked against that line/order.
- When enabled, a production receipt must reference a released work order in the same company; output item, variant, and destination location must match the work order.
- Added policy tests for unlinked production movements and nonexistent material-line references. These are source changes only; the self-hosted Release Gate must pass before the workflow is considered verified.

## Company date-format coverage — 2026-10-22

- Hardened `getCompanyDateFormat` so the entire local-storage read path is guarded; restricted browser contexts fall back to the default format rather than throwing.
- Applied the company-scoped date-format hook to the Sales and Purchasing document lists and added a visible document-date column to both.
- Applied the same formatter to HR attendance dates, overtime dates, and leave-request date ranges. Attendance check-in/out timestamps remain formatted separately with the company timezone because they represent instants, not calendar-only dates.
- This is incremental UI coverage only. Other modules, report layouts, and export formats have not all been migrated; therefore `general.date_format` remains catalog-only until the remaining consumers are covered and verified.
- GitHub Actions for the latest source change is queued/pending. Frontend typecheck/build and automated tests have not been confirmed successful in this environment.


## Company settings storage resilience — 2026-10-22

- The Company Policy Settings page now reads the initial selected company ID through a guarded helper. If browser storage is unavailable or contains an invalid/non-positive ID, the page falls back to company selection instead of throwing during initial render.
- This complements the guarded company date-format storage helper. It does not replace server-side company authorization; API permissions and company scoping remain the security boundary.
- Validation status: source change committed; local typecheck/build and latest self-hosted CI have not yet been confirmed.


## Local date-input defaults — 2026-10-22

- Added a shared `getLocalISODate()` helper so date inputs use the browser's local calendar date rather than slicing a UTC ISO timestamp.
- Updated Sales and Purchasing document creation defaults to use the helper, preventing the initial document date from shifting to yesterday/tomorrow around timezone boundaries.
- This is a date-input correctness fix; the company display format still applies to rendered list dates and does not alter the ISO date sent to the API.
- Validation status: committed source changes; typecheck/build and automated tests remain unconfirmed until a current workflow completes.


## Treasury local date-input defaults — 2026-10-22

- Updated the treasury cheque form's cheque date and due date defaults to use the shared `getLocalISODate()` helper, avoiding UTC date rollover in local date inputs.
- The cheque date values remain ISO calendar dates in the API payload; company display formatting is still used for the cheque due-date column.
- Validation status: source committed; frontend typecheck/build and automated CI results remain unconfirmed.


## Bank reconciliation local date-input defaults — 2026-10-22

- Updated bank reconciliation statement period dates and bank transaction date defaults to use the shared local-calendar date helper rather than UTC ISO slicing.
- Date-only values continue to be sent as ISO calendar dates to the API; statement period-end and transaction-date display remain company-format aware.
- Follow-up review found that financial report date filters are submitted as date-only values and do not render date output in the inspected page. The reports delivery schedule displays `next_run_at` as a timestamp, so it should retain timestamp/timezone semantics rather than be treated as a calendar-only date.
- Validation status: source committed; typecheck/build and automated checks remain unconfirmed.


## AR/AP aging local date default — 2026-10-22

- Updated `frontend/src/modules/accounting/pages/ARAgingPage.tsx` to initialize the “as of” date with the shared `getLocalISODate` helper rather than slicing `toISOString()`. This prevents UTC conversion from selecting the previous/next calendar date near local midnight.
- API date-only contract remains `YYYY-MM-DD`; aging row document/due dates continue using the company date-format helper.
- Validation status: source change committed; automated CI and local frontend/backend tests have not been confirmed in this turn.


## Report page company-id storage resilience — 2026-10-22

- `frontend/src/modules/reports/pages/ReportsPage.tsx` now reads the cached company ID through a guarded helper. If browser storage is unavailable, blocked, malformed, or contains a non-positive/non-integer ID, the page starts with company ID `0` and existing explicit “choose an active company” guards remain in force.
- This is a frontend resilience improvement only; it does not replace backend company authorization or tenant isolation.
- Validation status: source change committed; automated CI and local tests remain unconfirmed.


## Financial reports company-id storage resilience — 2026-10-22

- `frontend/src/modules/accounting/reports/FinancialReportsPage.tsx` now uses a guarded company-ID reader. Unavailable browser storage and invalid/non-positive IDs resolve to `0`; the existing page guard then requests an explicit active company instead of allowing a storage exception to break initialization.
- This client-side fallback is not an authorization boundary. Backend company scoping and permission checks remain mandatory.
- Validation status: source change committed; CI is queued/pending and local tests have not been run in this session.


## Journal entries local date and storage defaults — 2026-10-22

- `frontend/src/modules/accounting/journal-entries/JournalEntriesPage.tsx` now initializes new journal-entry dates through shared `getLocalISODate()`, preserving local calendar semantics for date-only accounting documents.
- The initial cached company ID is now read through a guarded helper. Unavailable browser storage or invalid/non-positive IDs resolve to `0`, and the existing active-company guard prevents loading/creating entries without a selected company.
- This is UI resilience, not an authorization boundary; backend tenant scoping remains required. CI is pending and no local tests were run in this session.


## Fiscal years company-storage resilience — 2026-10-22

- `frontend/src/modules/accounting/pages/FiscalYearsPage.tsx` now reads the cached active company through a guarded helper; blocked/unavailable browser storage and invalid IDs safely resolve to `0`.
- Existing company guard blocks list loading and disables creating a fiscal year when no valid company is selected. Backend authorization and company scoping remain mandatory; this frontend guard is not a security boundary.
- Validation status remains pending in GitHub Actions; this change has not been locally built or tested in this session.


## Commerce operational dates and storage guard — 2026-10-22

- `frontend/src/modules/commerce/pages/OperationalPage.tsx` now uses the shared local-calendar date helper for document creation, payment dates, payment reversals, and cheque due-date defaults; API date-only fields remain ISO `YYYY-MM-DD` values.
- The active-company lookup is guarded against blocked/unavailable browser storage and returns no selected company rather than throwing. Existing page guards stop company-scoped operations when no valid company is selected.
- This improves one shared commerce page used by sales/purchasing operations; it does not complete app-wide `general.date_format` coverage. CI and local tests remain unconfirmed.


## Additional local-calendar date defaults — 2026-10-22

- `frontend/src/modules/hr/pages/HrPage.tsx` now uses the shared local date helper for date-only leave defaults and guards active-company storage reads; unavailable storage results in no selected company.
- `frontend/src/modules/pos/pages/PosPage.tsx` now uses the same local-calendar helper for POS payment dates, preserving the API's date-only ISO contract without UTC rollover.
- These are incremental date-input fixes; they do not complete the global `general.date_format` display/export migration. CI and local tests remain unconfirmed.


## Inventory transaction date-format coverage — 2026-10-22

- `frontend/src/modules/inventory/pages/InventoryTransactionsPage.tsx` now displays the stock movement's date-only `transaction_date` using the shared company date-format hook and formatter; null dates display as an em dash.
- This extends the date-format migration but does not complete app-wide reports/exports or every date-bearing screen. `general.date_format` remains catalog-only until a wider consumer inventory and verification are complete.
- Source-level change committed. Frontend build, tests, and runtime verification remain unconfirmed.


## Shipping settlement local date default — 2026-10-22

- `frontend/src/modules/shipping/pages/ShippingSettlementPage.tsx` now initializes the settlement date with `getLocalISODate()` instead of slicing a UTC ISO timestamp, avoiding local-calendar rollover.
- The saved/API date remains an ISO date-only value. Existing settlement list display uses the company date formatter.
- This is an incremental completion of the date-format/date-input pass, not full coverage. CI/build and runtime validation remain unconfirmed.


## Authoritative company clock endpoint — 2026-10-22

- Added `GET /company-settings/clock?company_id=<id>`, protected by `company.access` and the same active-company/tenant validation as company settings. It returns UTC server time, configured company timezone, and the company-local calendar date.
- Extracted timezone conversion to `company_clock_payload`; added unit tests for timezone date rollover, naive datetime rejection, and invalid timezone rejection.
- Important limitation: this endpoint uses the application host's system clock. The host/VM/container must have correct time synchronization (NTP/host clock); an API cannot compensate for a wrong server clock without a trusted external time source.
- Frontend date-input defaults have not yet been migrated to fetch this endpoint, so existing `getLocalISODate()` still depends on the device clock until the client-side integration is implemented. Backend tests/build and runtime verification have not been run in this session.


## Device clock independence — company server clock integration — 2026-10-22

- Added `useCompanyClockDate(companyId?)` in `frontend/src/utils/format-date.ts`. It requests the authenticated `GET /company-settings/clock` endpoint and accepts only a valid ISO calendar date returned as `company_date`.
- It deliberately does **not** fall back to the device clock. If the company is not selected, access is denied, the API is offline, or the response is invalid, it returns an empty date and an error; transaction forms remain blank/blocked rather than silently using an unreliable date.
- Migrated date defaults for sales documents, purchase documents, journal entries, HR hire/leave/attendance forms, treasury cheque dates, bank reconciliation statement/line dates, shipping settlements, and the AR/AP aging “as of” date. POS checkout now uses the company server date and refuses to queue/submit a sale when that date cannot be obtained.
- Existing date-only values remain `YYYY-MM-DD` for HTML date inputs and API payloads; company display formatting remains a separate concern.
- **Clock trust boundary:** the endpoint returns the application server/container clock converted to the configured company timezone. This removes dependence on a user's incorrect device clock, but it cannot correct a wrong server clock. Host/container time synchronization (NTP or equivalent) must be monitored. An external trusted time provider would be a separate infrastructure decision.
- Validation: source changes committed; frontend build, unit tests, API authorization, and runtime behavior still require verification. Do not consider the date-format setting fully wired across every report/export based on this clock work alone.


## Server-authoritative company date defaults — 2026-10-22

- Date-only defaults on the migrated sales, purchasing, HR, treasury, bank reconciliation, AR/AP aging, and POS screens are populated from the authenticated `GET /company-settings/clock` endpoint using the company's configured IANA timezone. The frontend clock hook does not fall back to the device clock when the server cannot be reached; date defaults remain blank and an error is surfaced.
- Fixed a backend wiring defect in `backend/app/modules/company_settings/router.py`: the clock endpoint referenced `get_company_setting` and `company_clock_payload` without importing/defining them. It now reads the timezone through the shared typed `policy` consumer and imports the existing `company_clock_payload` implementation.
- Added a focused test for the company clock endpoint's timezone-policy wiring in `backend/tests/test_company_settings_consumers.py`.
- Important limit: this protects against an incorrect device clock, not an incorrect application-server/host clock. The host/container clock must be synchronized with NTP; the endpoint reports application-server time and does not independently verify an external time source.
- Automated test/build status has not yet been confirmed for this commit.


## Company date-format policy is now server-backed — 2026-10-22

- Added authenticated `GET /company-settings/date-format?company_id=...`, which validates active-company/tenant access and returns the validated `general.date_format` policy.
- `frontend/src/utils/format-date.ts` now refreshes the company date-format preference from that endpoint when the hook mounts, then caches the validated result locally for resilience. This removes the requirement to visit the policy-settings page first for date-format preferences to take effect.
- Added backend tests for the three supported formats and invalid stored values.
- This improves the shared formatter consumers but does not claim every date-bearing page, report, export, or printed document has been migrated. Host/server clock accuracy still depends on NTP; browser device time is not used for migrated date-only defaults.
- Build and automated test results are pending confirmation.


## Device-clock independence for fiscal-year defaults — 2026-10-22

- `frontend/src/modules/accounting/pages/FiscalYearsPage.tsx` no longer seeds fiscal-year code, labels, or start/end dates from `new Date().getFullYear()` on the user's device.
- Defaults are populated only after `useCompanyClockDate(companyId)` returns a validated `company_date` from the authenticated backend endpoint, which computes the date in the selected company's configured timezone.
- If the clock endpoint fails, the page surfaces the clock error and leaves defaults blank rather than silently trusting an incorrect device clock; users can still enter values manually.
- The backend endpoint uses the application host's UTC clock, so reliable host NTP/time synchronization is still an operational prerequisite. This protects against a wrong client/device clock; it cannot correct a wrong server clock.
- No local frontend build or runtime test was performed in this session; GitHub Actions is still pending/in progress at the time of this change.


## Approval escalation worker implementation — 2026-10-22

- Added `backend/app/jobs/approval_escalation.py`, a continuously polling worker that evaluates the company-specific `workflow.escalation_after_hours` policy for pending approval requests and queues one idempotent in-app reminder per still-pending approver/request.
- Added `approval-escalation-worker` to `docker-compose.yml`; it waits for the migration service to complete and uses the existing database configuration. Poll interval is configurable via `APPROVAL_ESCALATION_POLL_SECONDS` (default 60 seconds, minimum 30).
- The worker does not bypass approval authorization or decide requests. It only queues reminders; SMTP/WhatsApp escalation routing and manager/backup approver resolution are not claimed as implemented. The worker is not yet verified in a running Docker environment and no CI result has been confirmed.
