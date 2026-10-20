# Company Policy Settings — Static Wiring Audit

Date: 2026-10-20  
Branch: `feature/primeerp-full-system-audit-20261020-v2`

## Result

- Catalog entries audited individually: **68**.
- Confirmed workflow consumers in this change: **35**.
- Visible/persisted options not yet enforced by their owning workflows: **33**.
- Confirmed runtime consumers: `inventory.allow_negative_stock` (stock-movement posting), `accounting.require_journal_approval` (journal posting), `general.timezone`, `general.base_currency`, `general.allow_multi_currency`, `general.require_cost_center` and `accounting.allow_backdated_entries` (journal creation), plus `integrations.retry_limit` and `integrations.webhook_signature_required` (integration retry and Salla webhook intake), `accounting.fiscal_year_start_month` (fiscal-year creation), `accounting.rounding_method` and `tax.default_tax_inclusive_pricing` (tax calculation), `workflow.allow_self_approval` (generic transaction approval), `inventory.require_bin_location` (stock movement creation), `general.branch_required` (generic transaction creation), and `accounting.period_lock_enabled` (journal posting), `sales.credit_limit_enforced` (customer credit exposure check), `purchasing.require_goods_receipt` (supplier-bill creation), `sales.default_payment_terms_days` / `purchasing.default_payment_terms_days` (sales invoices and supplier bills when partner terms are unset), `crm.duplicate_customer_check` (customer creation by email/tax number), `pos.allow_discount_without_approval` / `pos.max_discount_pct_without_approval` (POS checkout discounts), `inventory.require_warehouse` (stockable/consumable commerce documents), `tax.require_tax_code_on_invoice` (taxable sales/purchase invoice lines), and `accounting.auto_post_sales_invoice` / `accounting.auto_post_purchase_invoice` (company-gated accounting auto-post), and the five `accounting.default_*_account` code settings (company-scoped active posting-account overrides for commerce AR, AP, sales, purchase expense, and payment/cash lines), and `purchasing.allow_invoice_price_variance` / `purchasing.price_variance_tolerance_pct` (supplier bill vs linked receipt valuation comparison at bill accounting posting). FIFO negative issues remain blocked for valuation safety, and reserved quantities remain protected.
- This is a source-level audit, not a successful runtime test. Docker is unavailable/offline for the user, and the GitHub self-hosted Release Gate is queued; no test-pass claim is made.

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
| `general.require_project` | bool | CATALOG ONLY | Require project dimension where supported |
| `general.branch_required` | bool | **RUNTIME** | Reject generic transaction creation without a branch when enabled |
| `general.intercompany_enabled` | bool | CATALOG ONLY | Enable intercompany workflows |

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
| `tax.einvoice_required_for_sales` | bool | CATALOG ONLY | Require Egyptian e-invoice submission for eligible sales |

## Sales (8)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `sales.require_quote_approval` | bool | CATALOG ONLY | Require quotation approval above configured limits |
| `sales.require_order_approval` | bool | CATALOG ONLY | Require sales order approval |
| `sales.invoice_requires_delivery` | bool | CATALOG ONLY | Require delivery before invoicing stock items |
| `sales.allow_overbilling` | bool | CATALOG ONLY | Allow billing above ordered quantity |
| `sales.credit_limit_enforced` | bool | **RUNTIME** | Apply customer credit-limit checks when enabled |
| `sales.allow_negative_customer_balance` | bool | CATALOG ONLY | Allow defined customer balance exceptions |
| `sales.default_payment_terms_days` | int | **RUNTIME** | Default due-date terms for sales invoices when partner terms are unset |
| `sales.document_numbering` | enum | CATALOG ONLY | Sales document numbering policy |

## Purchasing (6)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `purchasing.require_purchase_order` | bool | CATALOG ONLY | Require PO before supplier invoice |
| `purchasing.require_purchase_approval` | bool | CATALOG ONLY | Require purchase order approval |
| `purchasing.require_goods_receipt` | bool | **RUNTIME** | Block supplier-bill creation without a validated receipt link when enabled |
| `purchasing.allow_invoice_price_variance` | bool | **RUNTIME** | Allow linked receipt-vs-bill stock valuation variance above the configured tolerance |
| `purchasing.price_variance_tolerance_pct` | number | **RUNTIME** | Maximum invoice-vs-receipt stock valuation variance percentage before the allow-beyond-tolerance switch is required |
| `purchasing.default_payment_terms_days` | int | **RUNTIME** | Default due-date terms for supplier bills when partner terms are unset |

## Inventory (9)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `inventory.allow_negative_stock` | bool | **RUNTIME** | Allow stock to fall below zero where the valuation method supports it |
| `inventory.valuation_method` | enum | CATALOG ONLY | Inventory costing method for supported flows |
| `inventory.require_warehouse` | bool | **RUNTIME** | Require a warehouse for stockable/consumable commerce document lines |
| `inventory.require_bin_location` | bool | **RUNTIME** | Require child/bin locations for stock movement endpoints |
| `inventory.auto_reserve_sales_orders` | bool | CATALOG ONLY | Reserve stock on sales order confirmation |
| `inventory.allow_below_cost_sale` | bool | CATALOG ONLY | Allow sale below cost subject to permission |
| `inventory.expiry_tracking_required` | bool | CATALOG ONLY | Require expiry dates for perishable/batch items |
| `inventory.serial_tracking_default` | bool | CATALOG ONLY | Default serial tracking for eligible items |
| `inventory.batch_tracking_default` | bool | CATALOG ONLY | Default batch/lot tracking for eligible items |

## Human Resources (8)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `hr.attendance_source` | enum | CATALOG ONLY | Attendance source |
| `hr.require_attendance_approval` | bool | CATALOG ONLY | Require attendance corrections approval |
| `hr.overtime_requires_approval` | bool | CATALOG ONLY | Require overtime approval |
| `hr.leave_requires_approval` | bool | CATALOG ONLY | Require leave approval |
| `hr.payroll_requires_approval` | bool | CATALOG ONLY | Require payroll approval before posting |
| `hr.allow_negative_leave_balance` | bool | CATALOG ONLY | Allow leave balance below zero |
| `hr.default_work_hours_per_day` | number | CATALOG ONLY | Default scheduled hours per workday |
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
| `pos.require_shift_close` | bool | CATALOG ONLY | Require cashier shift closing and reconciliation |
| `pos.allow_discount_without_approval` | bool | **RUNTIME** | Permit discounts above the no-approval threshold when enabled |
| `pos.max_discount_pct_without_approval` | number | **RUNTIME** | Enforce maximum POS discount percentage when approval-free discounts are disabled |

## Manufacturing (2)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `manufacturing.require_work_order` | bool | CATALOG ONLY | Require work order for production |
| `manufacturing.allow_overproduction` | bool | CATALOG ONLY | Allow production above planned quantity |

## CRM (1)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `crm.duplicate_customer_check` | bool | **RUNTIME** | Block active customer duplicates by matching normalized email or tax number when enabled |

## Integrations (3)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `integrations.auto_sync_enabled` | bool | CATALOG ONLY | Enable automatic sync for configured integrations |
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

## Recommended order for full wiring

1. Accounting controls: backdated journal creation, base currency, foreign-currency allowance, required cost centers, journal approval, fiscal-year start month, tax rounding and default tax-inclusive pricing are now enforced. Closed-period controls remain authoritative; default accounts and auto-posting still require workflow wiring.
2. Sales and procurement: approval rules, delivery/receipt requirements, customer credit limits, overbilling and price variance tolerances. Generic transaction creation now enforces `general.branch_required` when enabled. Journal posting consumes `accounting.period_lock_enabled` to control closed-period status/allow-posting enforcement. Commerce workflows now honor `sales.credit_limit_enforced` and `purchasing.require_goods_receipt`; tax calculation uses the company tax-inclusive default and stores the extracted taxable base correctly. Sales and supplier documents also apply company default payment terms when the partner has no explicit terms, and CRM partner creation blocks likely duplicate active customers when the duplicate-check policy is enabled. POS checkout blocks discounts when approval is required (no approval-capture flow exists) and enforces the maximum discount percentage when approval-free discounts are enabled. Commerce documents reject stockable/consumable lines without a warehouse when the company requires one, and taxable invoice lines cannot explicitly omit their configured tax codes when the policy is enabled.
3. Inventory: warehouse/bin requirements, reservation behavior, below-cost sales, serial/batch/expiry, and valuation method consistency.
4. HR: biometric device ingestion, attendance correction/overtime/leave/payroll approvals, leave balances and work schedules.
5. POS, manufacturing, CRM and integrations: cashier shift close, discount limits, work orders, duplicate checks, retry policy and signed webhooks.

A setting should be promoted from CATALOG ONLY to RUNTIME only after the consumer is wired, company-isolation tests pass, and positive/negative workflow tests prove the behavior.


## Settings UI organization update
- Company policies remain grouped by category in registry order. Within a category, runtime-enforced entries are listed before catalog-only entries, then labels are alphabetically sorted using Arabic locale rules.
- The page now searches by display label, canonical setting key, module, and translated category/module names; a status filter narrows results to runtime or catalog-only entries.
- The page shows total/runtime/catalog/unsaved-change counters, a result count, a reset control, an empty-result message, and disables Save when no values differ from the loaded values.
- These UX changes improve navigation. The current source audit records **27 runtime / 41 catalog-only** after adding transaction branch requirements, journal period-lock policy, customer credit-limit enforcement, supplier receipt requirements, company payment-term defaults, duplicate-customer checks, POS discount policy enforcement, warehouse requirements, taxable invoice tax-code enforcement, and accounting auto-post gates; tests still need to run.


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
- `integrations.auto_sync_enabled`: the Salla full-sync path found in this review is an explicitly invoked API endpoint, not an automatic scheduler. This option must not block manual sync or be represented as active until an automatic sync runner exists.
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

The 33 catalog-only settings below are the remaining candidates for workflow wiring. Grouping is by the primary workflow needed; it is not a claim that the work is already implemented.

### A. Company defaults and accounting configuration (8)
- `general.date_format`: apply the selected format consistently through shared frontend date-formatting utilities; enum validation is covered, but display-wide wiring is not yet complete.
- `general.require_project`: add project dimension to the supported document schemas and persistence first.
- `general.intercompany_enabled`: implement intercompany transaction lifecycle, balancing, and cross-company permissions.

### B. Tax and Egyptian e-invoice (1)
- `tax.einvoice_required_for_sales`: enforce submission/acceptance requirements at the sales document finalization boundary; define failure/retry behavior and exemptions before blocking transactions.

### C. Sales and customer rules (6)
- `sales.require_quote_approval`, `sales.require_order_approval`: add explicit draft → pending approval → approved/rejected transitions, approver permissions, audit history and tests.
- `sales.invoice_requires_delivery`, `sales.allow_overbilling`: introduce reliable order-line ↔ delivery-line ↔ invoice-line allocation and quantity accounting; do not infer relationships by customer alone.
- `sales.allow_negative_customer_balance`: define which transaction types and permissions may create negative balances, then enforce in the credit/balance service.
- `sales.document_numbering`: implement company/year sequence generation with transaction-safe allocation and uniqueness constraints/migration.

### D. Purchasing and supplier controls (2)
- `purchasing.require_purchase_order`, `purchasing.require_purchase_approval`: persist purchase-order source links and approval lifecycle before enforcing supplier-bill restrictions.

### E. Inventory and costing (6)
- `inventory.valuation_method`: verify all issue/receipt/return/adjustment paths share a consistent company costing strategy; requires migration/revaluation strategy if existing stock has balances.
- `inventory.auto_reserve_sales_orders`: add atomic reservation records and release/expiry behavior on cancellation, edits and fulfillment.
- `inventory.allow_below_cost_sale`: enforce using current valuation cost and explicit permission/audit behavior at sales-line validation.
- `inventory.expiry_tracking_required`, `inventory.serial_tracking_default`, `inventory.batch_tracking_default`: connect item tracking flags to receipt, stock movement, lot/serial identity and issue validation; defaults should affect new items only unless a migration is deliberately approved.

### F. HR (8)
- `hr.attendance_source`, `hr.biometric_sync_interval_minutes`: add supported source adapters and a scheduler/worker with per-company configuration.
- `hr.require_attendance_approval`, `hr.overtime_requires_approval`, `hr.leave_requires_approval`, `hr.payroll_requires_approval`: implement approval states and role checks in each corresponding HR lifecycle before marking runtime.
- `hr.allow_negative_leave_balance`: enforce at leave request/approval and concurrent balance update.
- `hr.default_work_hours_per_day`: use as a company fallback in schedules and overtime calculations where an employee-specific schedule is absent.

### G. Approval engine and operations (2)
- `workflow.approval_mode`, `workflow.escalation_after_hours`: complete the approval engine (sequential/parallel/any-one decisions, due-time tracking, escalation jobs and audit trail). Do not wire these to UI labels alone.

### H. POS and manufacturing (4)
- `pos.allow_open_cash_drawer`, `pos.require_shift_close`: add permission-checked cash-drawer events and enforced shift close/reconciliation before session finalization.
- `manufacturing.require_work_order`, `manufacturing.allow_overproduction`: enforce work-order linkage and planned-vs-produced quantity at production completion, with stock/ledger consistency.

### I. Integrations (1)
- `integrations.auto_sync_enabled`: implement a per-company scheduled sync worker, locking/idempotency and failure handling. Keep manual sync available regardless of this setting; the toggle should control scheduled runs only.

### Recommended execution sequence
1. Low-dependency defaults: date/language presentation, account-code fallback resolution, workday/payment defaults where their owning service already exists.
2. Sales/purchasing lifecycle foundations: document approval states and source-line relationships, followed by delivery/overbilling and PO/price variance policies.
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
