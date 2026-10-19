# PrimeERP — Company Policy Settings Architecture (2026-10-20)

## Goal
Company-specific business policies must be data/configuration, not customer-specific code forks. Each company stores its own values; a value for one company must never leak to another. The catalog is centrally typed and allow-listed: clients cannot create arbitrary setting keys or write credentials into the policy table.

## Current implementation in this change
- Company-scoped persistence table: `company_settings`, unique by `(company_id, setting_key)`.
- API: `GET /api/v1/company-settings?company_id=N` and `PUT /api/v1/company-settings?company_id=N`.
- Company is checked against the caller's effective tenant and must be active.
- Read requires `company.access`; write requires `company.write`.
- Unknown keys, extra request fields, invalid data types and invalid enum choices are rejected.
- Changes emit an audit event listing changed setting keys (not values or secrets).
- Frontend page at `/settings/company-policies` groups options by module/category and persists only changed values.
- `inventory.allow_negative_stock` is consumed by stock-movement posting. It remains disabled by default. Even when enabled, negative stock is blocked for FIFO valuation because FIFO layer consumption cannot safely value an issue with insufficient layers.
- This branch has not been runtime-tested locally; the user's Docker/local machine is offline. CI must validate migration graph, API tests and frontend build before pull.

## Catalog coverage
The typed registry currently exposes 66 options across General, Accounting, Taxes, Sales, Purchasing, Inventory, HR, Approvals, POS, Manufacturing, CRM, Integrations, and Audit. Exact keys and defaults are in `backend/app/modules/company_settings/registry.py`.

### General
- Language, date format, timezone, functional currency, multi-currency, mandatory cost center/project, mandatory branch, intercompany transactions.
### Accounting and tax
- Period lock, backdated posting, journal approval, automatic invoice posting, rounding, fiscal-year start, default receivable/payable/sales/purchase/cash accounts, tax-inclusive pricing, tax code requirement and Egyptian e-invoice requirement.
### Sales and purchasing
- Quotation/order approval, delivery-before-invoice, overbilling, credit-limit enforcement, payment terms, document numbering; PO/receipt requirements, purchase approvals, invoice price variance and tolerance.
### Inventory
- Negative stock, valuation method, warehouse/bin requirements, order reservations, below-cost sales, expiry, serial and batch tracking.
### HR
- Attendance source (manual/biometric/mobile/integration), correction/overtime/leave/payroll approvals, negative leave balance, scheduled hours and biometric sync interval.
### Workflow, POS and operations
- Approval mode, self-approval, escalation, POS cash drawer, shift close, discount approvals/limits, work orders, overproduction and duplicate customer checks.
### Integrations
- Automatic sync, retry count and webhook signature requirement. API keys, OAuth secrets, passwords, tokens and device credentials are deliberately excluded and must live in a separate encrypted integration credential store.

## Critical status distinction
A catalog entry being visible and saved does not mean its effect has been wired into every business transaction. Only entries marked `runtime` have a consumer in this change. Entries marked `catalog` are editable policy definitions and are not yet enforced by the owning module. They must not be advertised as operational until module-specific integration tests prove the effect.

## Required next integrations
1. Accounting: period-close guard, approval thresholds, posting defaults, fiscal-year policy and immutable audit behavior.
2. Sales/purchasing: quote/order/PO/receipt requirements, credit limit and variance tolerances.
3. Inventory: costing method consistency, reservations, batch/serial/expiry and warehouse/bin requirements.
4. HR: employee lifecycle, biometric device adapters, attendance corrections, leave, payroll and approvals.
5. POS/manufacturing/CRM: shift close, discounts, work orders and duplicate checks.
6. Integrations: provider-specific sync policies and encrypted credentials.
7. Settings admin UX: permissions, validation warnings, impact preview, effective-date policy and a settings change history screen.

## Configuration precedence
Use a deterministic order: system safety/legal constraints > tenant plan entitlements > company policy > branch policy (where supported) > document-specific override (only when permitted) > user/session defaults. A lower-level setting must never override statutory controls, authorization, tenant boundaries or a closed accounting period.

## Safe rollout rule
Never rewrite posted documents merely because a policy changed. Changes apply prospectively unless a separately approved migration/recalculation process explicitly supports historical changes.
