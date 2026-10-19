# Company Policy Settings — Static Wiring Audit

Date: 2026-10-20
Branch: `feature/primeerp-full-system-audit-20261020-v2`

## Result

- Catalog entries found: 68.
- Confirmed workflow consumers in this change: 1.
- Visible/persisted options not yet enforced by their owning workflows: 67.
- The only confirmed runtime consumer is `inventory.allow_negative_stock`, read during stock-movement posting. FIFO negative issues remain blocked for valuation safety, and reserved quantities remain protected.
- This is a source-level audit, not a successful runtime test. Docker is unavailable/offline for the user, and the GitHub self-hosted Release Gate is queued; no test-pass claim is made.

## How to read the results

- **RUNTIME**: code path found that reads this setting and changes/enforces workflow behavior (subject to its documented guardrails).
- **CATALOG ONLY**: UI, API, storage, and type validation exist, but a source-level workflow consumer has not been verified. It must not be treated as active business logic.

## General

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `general.default_language` | enum | CATALOG ONLY | Interface language",["ar |
| `general.date_format` | enum | CATALOG ONLY | MM/DD/YYYY |
| `general.timezone` | string | CATALOG ONLY | Company timezone |
| `general.base_currency` | string | CATALOG ONLY | Functional currency code |

## Accounting

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `accounting.rounding_method` | enum | CATALOG ONLY | bankers |
| `accounting.default_receivable_account` | string | CATALOG ONLY | Default receivable account code |
| `accounting.default_payable_account` | string | CATALOG ONLY | Default payable account code |
| `accounting.default_sales_account` | string | CATALOG ONLY | Default sales account code |
| `accounting.default_purchase_account` | string | CATALOG ONLY | Default purchase account code |
| `accounting.default_cash_account` | string | CATALOG ONLY | Default cash account code |

## Sales

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `sales.document_numbering` | enum | CATALOG ONLY | per_company |

## Inventory

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `inventory.valuation_method` | enum | CATALOG ONLY | moving_average |

## Human Resources

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `hr.attendance_source` | enum | CATALOG ONLY | mobile |

## Approvals

| Option key | Type | Current status | Purpose |
|---|---|---|---|
| `workflow.approval_mode` | enum | CATALOG ONLY | parallel |

## Defects and improvements made during this audit

1. Validation now rejects unknown setting keys, invalid enum values, wrong booleans, non-finite numbers (NaN/Infinity), invalid IANA time zones, malformed 3-letter uppercase currency codes, out-of-range fiscal year months, and workday lengths outside 0–24 hours.
2. Added parameterized tests that validate every catalog default and key boundary cases. These tests are committed but have **not yet been executed successfully** in CI.
3. The UI distinguishes runtime-enabled settings from catalog-only settings, so saving a value does not falsely imply that a business workflow uses it.
4. Company settings writes are tenant-scoped, permission-protected, and audited by changed key names without recording values or credentials.

## Per-option status

Every row in the tables above is an individual audit result. At this stage, all 67 catalog-only options are **not yet confirmed operational**. They need workflow-specific tests before promotion to runtime. Do not mark them active based only on successful save/read API calls.

## Recommended order for full wiring

1. Accounting controls: closed-period posting, backdated journals, approvals, default accounts, rounding and fiscal-year policies.
2. Sales and procurement: approval rules, delivery/receipt requirements, customer credit limits, overbilling and price variance tolerances.
3. Inventory: warehouse/bin requirements, reservation behavior, below-cost sales, serial/batch/expiry, and valuation method consistency.
4. HR: biometric device ingestion, attendance correction/overtime/leave/payroll approvals, leave balances and work schedules.
5. POS, manufacturing, CRM and integrations: cashier shift close, discount limits, work orders, duplicate checks, retry policy and signed webhooks.

A setting should be promoted from CATALOG ONLY to RUNTIME only after the consumer is wired, company-isolation tests pass, and positive/negative workflow tests prove the behavior.
