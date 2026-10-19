# Company Policy Settings — Static Wiring Audit

Date: 2026-10-20  
Branch: `feature/primeerp-full-system-audit-20261020-v2`

## Result

- Catalog entries audited individually: **68**.
- Confirmed workflow consumers in this change: **2**.
- Visible/persisted options not yet enforced by their owning workflows: **66**.
- Confirmed runtime consumers are `inventory.allow_negative_stock` (stock-movement posting) and `accounting.require_journal_approval` (journal posting). Journal posting now checks the company policy in addition to the journal-specific approval rule. FIFO negative issues remain blocked for valuation safety, and reserved quantities remain protected.
- This is a source-level audit, not a successful runtime test. Docker is unavailable/offline for the user, and the GitHub self-hosted Release Gate is queued; no test-pass claim is made.

## Status definitions

- **RUNTIME**: code path found that reads this setting and changes/enforces workflow behavior, with documented guardrails.
- **CATALOG ONLY**: UI, API, storage and type validation exist, but no workflow consumer was verified. It must not be treated as active business logic.

## General (9)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `general.default_language` | enum | CATALOG ONLY | Interface language |
| `general.date_format` | enum | CATALOG ONLY | Date display format |
| `general.timezone` | string | CATALOG ONLY | Company timezone |
| `general.base_currency` | string | CATALOG ONLY | Functional currency code |
| `general.allow_multi_currency` | bool | CATALOG ONLY | Allow foreign-currency transactions |
| `general.require_cost_center` | bool | CATALOG ONLY | Require cost center where supported |
| `general.require_project` | bool | CATALOG ONLY | Require project dimension where supported |
| `general.branch_required` | bool | CATALOG ONLY | Require branch on company transactions |
| `general.intercompany_enabled` | bool | CATALOG ONLY | Enable intercompany workflows |

## Accounting (12)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `accounting.period_lock_enabled` | bool | CATALOG ONLY | Prevent posting into closed periods |
| `accounting.allow_backdated_entries` | bool | CATALOG ONLY | Allow backdated entries subject to period controls |
| `accounting.require_journal_approval` | bool | **RUNTIME** | Require approval before journal posting |
| `accounting.auto_post_sales_invoice` | bool | CATALOG ONLY | Automatically post eligible sales invoices |
| `accounting.auto_post_purchase_invoice` | bool | CATALOG ONLY | Automatically post eligible purchase invoices |
| `accounting.rounding_method` | enum | CATALOG ONLY | Document rounding policy |
| `accounting.fiscal_year_start_month` | int | CATALOG ONLY | First month of fiscal year |
| `accounting.default_receivable_account` | string | CATALOG ONLY | Default receivable account code |
| `accounting.default_payable_account` | string | CATALOG ONLY | Default payable account code |
| `accounting.default_sales_account` | string | CATALOG ONLY | Default sales account code |
| `accounting.default_purchase_account` | string | CATALOG ONLY | Default purchase account code |
| `accounting.default_cash_account` | string | CATALOG ONLY | Default cash account code |

## Taxes (3)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `tax.default_tax_inclusive_pricing` | bool | CATALOG ONLY | Sales prices include tax by default |
| `tax.require_tax_code_on_invoice` | bool | CATALOG ONLY | Require tax code on taxable invoices |
| `tax.einvoice_required_for_sales` | bool | CATALOG ONLY | Require Egyptian e-invoice submission for eligible sales |

## Sales (8)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `sales.require_quote_approval` | bool | CATALOG ONLY | Require quotation approval above configured limits |
| `sales.require_order_approval` | bool | CATALOG ONLY | Require sales order approval |
| `sales.invoice_requires_delivery` | bool | CATALOG ONLY | Require delivery before invoicing stock items |
| `sales.allow_overbilling` | bool | CATALOG ONLY | Allow billing above ordered quantity |
| `sales.credit_limit_enforced` | bool | CATALOG ONLY | Block orders beyond customer credit limit |
| `sales.allow_negative_customer_balance` | bool | CATALOG ONLY | Allow defined customer balance exceptions |
| `sales.default_payment_terms_days` | int | CATALOG ONLY | Default customer payment term |
| `sales.document_numbering` | enum | CATALOG ONLY | Sales document numbering policy |

## Purchasing (6)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `purchasing.require_purchase_order` | bool | CATALOG ONLY | Require PO before supplier invoice |
| `purchasing.require_purchase_approval` | bool | CATALOG ONLY | Require purchase order approval |
| `purchasing.require_goods_receipt` | bool | CATALOG ONLY | Require receipt before supplier invoice |
| `purchasing.allow_invoice_price_variance` | bool | CATALOG ONLY | Allow invoice price variance beyond tolerance |
| `purchasing.price_variance_tolerance_pct` | number | CATALOG ONLY | Allowed price variance percentage |
| `purchasing.default_payment_terms_days` | int | CATALOG ONLY | Default supplier payment term |

## Inventory (9)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `inventory.allow_negative_stock` | bool | **RUNTIME** | Allow stock to fall below zero where the valuation method supports it |
| `inventory.valuation_method` | enum | CATALOG ONLY | Inventory costing method for supported flows |
| `inventory.require_warehouse` | bool | CATALOG ONLY | Require warehouse on stock transactions |
| `inventory.require_bin_location` | bool | CATALOG ONLY | Require a storage/bin location |
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
| `workflow.allow_self_approval` | bool | CATALOG ONLY | Allow requester to approve their own request |
| `workflow.escalation_after_hours` | int | CATALOG ONLY | Escalate pending approvals after hours |

## Point of Sale (4)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `pos.allow_open_cash_drawer` | bool | CATALOG ONLY | Allow cash drawer opening without a transaction |
| `pos.require_shift_close` | bool | CATALOG ONLY | Require cashier shift closing and reconciliation |
| `pos.allow_discount_without_approval` | bool | CATALOG ONLY | Allow cashier discounts without approval |
| `pos.max_discount_pct_without_approval` | number | CATALOG ONLY | Maximum discount without approval |

## Manufacturing (2)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `manufacturing.require_work_order` | bool | CATALOG ONLY | Require work order for production |
| `manufacturing.allow_overproduction` | bool | CATALOG ONLY | Allow production above planned quantity |

## CRM (1)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `crm.duplicate_customer_check` | bool | CATALOG ONLY | Warn/block likely duplicate customers |

## Integrations (3)

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `integrations.auto_sync_enabled` | bool | CATALOG ONLY | Enable automatic sync for configured integrations |
| `integrations.retry_limit` | int | CATALOG ONLY | Retry count for transient integration failures |
| `integrations.webhook_signature_required` | bool | CATALOG ONLY | Require signatures for supported inbound webhooks |

## Defects and improvements made during this audit

1. Validation now rejects unknown setting keys, invalid enum values, wrong booleans, non-finite numbers (NaN/Infinity), invalid IANA time zones, malformed 3-letter uppercase currency codes, out-of-range fiscal year months, and workday lengths outside 0–24 hours.
2. Added parameterized tests that validate every catalog default and key boundary cases. These tests are committed but have **not yet been executed successfully** in CI.
3. The UI distinguishes runtime-enabled settings from catalog-only settings, so saving a value does not falsely imply that a business workflow uses it.
4. Company settings writes are tenant-scoped, permission-protected, and audited by changed key names without recording values or credentials.

## Recommended order for full wiring

1. Accounting controls: closed-period posting, backdated journals, default accounts, rounding and fiscal-year policies. Journal approval is now enforced from company policy; remaining controls still require workflow wiring.
2. Sales and procurement: approval rules, delivery/receipt requirements, customer credit limits, overbilling and price variance tolerances.
3. Inventory: warehouse/bin requirements, reservation behavior, below-cost sales, serial/batch/expiry, and valuation method consistency.
4. HR: biometric device ingestion, attendance correction/overtime/leave/payroll approvals, leave balances and work schedules.
5. POS, manufacturing, CRM and integrations: cashier shift close, discount limits, work orders, duplicate checks, retry policy and signed webhooks.

A setting should be promoted from CATALOG ONLY to RUNTIME only after the consumer is wired, company-isolation tests pass, and positive/negative workflow tests prove the behavior.
