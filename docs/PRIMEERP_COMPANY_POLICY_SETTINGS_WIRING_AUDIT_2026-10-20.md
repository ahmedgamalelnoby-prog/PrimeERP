# Company Policy Settings — Static Wiring Audit

Date: 2026-10-20  
Branch: `feature/primeerp-full-system-audit-20261020-v2`

## Result

- Catalog entries audited individually: **68**.
- Confirmed workflow consumers in this change: **23**.
- Visible/persisted options not yet enforced by their owning workflows: **45**.
- Confirmed runtime consumers: `inventory.allow_negative_stock` (stock-movement posting), `accounting.require_journal_approval` (journal posting), `general.timezone`, `general.base_currency`, `general.allow_multi_currency`, `general.require_cost_center` and `accounting.allow_backdated_entries` (journal creation), plus `integrations.retry_limit` and `integrations.webhook_signature_required` (integration retry and Salla webhook intake), `accounting.fiscal_year_start_month` (fiscal-year creation), `accounting.rounding_method` and `tax.default_tax_inclusive_pricing` (tax calculation), `workflow.allow_self_approval` (generic transaction approval), `inventory.require_bin_location` (stock movement creation), `general.branch_required` (generic transaction creation), and `accounting.period_lock_enabled` (journal posting), `sales.credit_limit_enforced` (customer credit exposure check), `purchasing.require_goods_receipt` (supplier-bill creation), `sales.default_payment_terms_days` / `purchasing.default_payment_terms_days` (sales invoices and supplier bills when partner terms are unset), `crm.duplicate_customer_check` (customer creation by email/tax number), and `pos.allow_discount_without_approval` / `pos.max_discount_pct_without_approval` (POS checkout discounts). FIFO negative issues remain blocked for valuation safety, and reserved quantities remain protected.
- This is a source-level audit, not a successful runtime test. Docker is unavailable/offline for the user, and the GitHub self-hosted Release Gate is queued; no test-pass claim is made.

## Status definitions

- **RUNTIME**: code path found that reads this setting and changes/enforces workflow behavior, with documented guardrails.
- **CATALOG ONLY**: UI, API, storage and type validation exist, but no workflow consumer was verified. It must not be treated as active business logic.

## General (9)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `general.default_language` | enum | CATALOG ONLY | Interface language |
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
| `accounting.auto_post_sales_invoice` | bool | CATALOG ONLY | Automatically post eligible sales invoices |
| `accounting.auto_post_purchase_invoice` | bool | CATALOG ONLY | Automatically post eligible purchase invoices |
| `accounting.rounding_method` | enum | **RUNTIME** | Tax calculation rounding mode |
| `accounting.fiscal_year_start_month` | int | **RUNTIME** | Enforce configured month when creating a fiscal year |
| `accounting.default_receivable_account` | string | CATALOG ONLY | Default receivable account code |
| `accounting.default_payable_account` | string | CATALOG ONLY | Default payable account code |
| `accounting.default_sales_account` | string | CATALOG ONLY | Default sales account code |
| `accounting.default_purchase_account` | string | CATALOG ONLY | Default purchase account code |
| `accounting.default_cash_account` | string | CATALOG ONLY | Default cash account code |

## Taxes (3)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `tax.default_tax_inclusive_pricing` | bool | **RUNTIME** | Default tax-inclusive behavior when caller does not explicitly choose |
| `tax.require_tax_code_on_invoice` | bool | CATALOG ONLY | Require tax code on taxable invoices |
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
| `purchasing.allow_invoice_price_variance` | bool | CATALOG ONLY | Allow invoice price variance beyond tolerance |
| `purchasing.price_variance_tolerance_pct` | number | CATALOG ONLY | Allowed price variance percentage |
| `purchasing.default_payment_terms_days` | int | **RUNTIME** | Default due-date terms for supplier bills when partner terms are unset |

## Inventory (9)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `inventory.allow_negative_stock` | bool | **RUNTIME** | Allow stock to fall below zero where the valuation method supports it |
| `inventory.valuation_method` | enum | CATALOG ONLY | Inventory costing method for supported flows |
| `inventory.require_warehouse` | bool | CATALOG ONLY | Require warehouse on stock transactions |
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

## Defects and improvements made during this audit

1. Validation now rejects unknown setting keys, invalid enum values, wrong booleans, non-finite numbers (NaN/Infinity), invalid IANA time zones, malformed 3-letter uppercase currency codes, out-of-range fiscal year months, and workday lengths outside 0–24 hours.
2. Added parameterized tests for every catalog default, key validation boundaries, company rounding modes, and self-approval policy. These tests are committed but have **not yet been executed successfully** locally or in CI.
3. The UI distinguishes runtime-enabled settings from catalog-only settings, so saving a value does not falsely imply that a business workflow uses it.
4. Company settings writes are tenant-scoped, permission-protected, and audited by changed key names without recording values or credentials.

## Recommended order for full wiring

1. Accounting controls: backdated journal creation, base currency, foreign-currency allowance, required cost centers, journal approval, fiscal-year start month, tax rounding and default tax-inclusive pricing are now enforced. Closed-period controls remain authoritative; default accounts and auto-posting still require workflow wiring.
2. Sales and procurement: approval rules, delivery/receipt requirements, customer credit limits, overbilling and price variance tolerances. Generic transaction creation now enforces `general.branch_required` when enabled. Journal posting consumes `accounting.period_lock_enabled` to control closed-period status/allow-posting enforcement. Commerce workflows now honor `sales.credit_limit_enforced` and `purchasing.require_goods_receipt`; tax calculation uses the company tax-inclusive default and stores the extracted taxable base correctly. Sales and supplier documents also apply company default payment terms when the partner has no explicit terms, and CRM partner creation blocks likely duplicate active customers when the duplicate-check policy is enabled. POS checkout validates discount percentages against company policy before creating the sale.
3. Inventory: warehouse/bin requirements, reservation behavior, below-cost sales, serial/batch/expiry, and valuation method consistency.
4. HR: biometric device ingestion, attendance correction/overtime/leave/payroll approvals, leave balances and work schedules.
5. POS, manufacturing, CRM and integrations: cashier shift close, discount limits, work orders, duplicate checks, retry policy and signed webhooks.

A setting should be promoted from CATALOG ONLY to RUNTIME only after the consumer is wired, company-isolation tests pass, and positive/negative workflow tests prove the behavior.


## Settings UI organization update
- Company policies remain grouped by category in registry order. Within a category, runtime-enforced entries are listed before catalog-only entries, then labels are alphabetically sorted using Arabic locale rules.
- The page now searches by display label, canonical setting key, module, and translated category/module names; a status filter narrows results to runtime or catalog-only entries.
- The page shows total/runtime/catalog/unsaved-change counters, a result count, a reset control, an empty-result message, and disables Save when no values differ from the loaded values.
- These UX changes improve navigation. The current source audit records **23 runtime / 45 catalog-only** after adding transaction branch requirements, journal period-lock policy, customer credit-limit enforcement, supplier receipt requirements, company payment-term defaults, duplicate-customer checks, and POS discount policy enforcement; tests still need to run.
