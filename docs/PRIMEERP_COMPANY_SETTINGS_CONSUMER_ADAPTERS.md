# PrimeERP — Company Settings Consumer Adapters

Branch: `feature/primeerp-full-system-audit-20261020-v2`

This package provides the first integration layer for the eight company settings still classified as catalog-only. It intentionally centralizes policy reads and deterministic decisions instead of duplicating registry lookups across domain modules.

## Adapters created

| Setting | Adapter | Expected owning workflow |
|---|---|---|
| `general.date_format` | `format_company_date(db, company_id, value)` | Shared frontend/report date formatting; backend helper is available for generated/exported output |
| `hr.attendance_source` | `attendance_source_allowed(db, company_id, source)` | Attendance create/import API; reject writes whose source conflicts with company policy |
| `hr.biometric_sync_interval_minutes` | `biometric_sync_due(db, company_id, last_sync_at, now=...)` | Biometric connector polling worker |
| `hr.payroll_requires_approval` | `payroll_approval_required(db, company_id)` | Payroll finalization/posting; leave payroll pending until an authorized decision |
| `workflow.approval_mode` | `approval_mode(db, company_id)` and `approval_plan(mode, approver_ids)` | Workflow engine; sequential, parallel, or any-one approval semantics |
| `workflow.escalation_after_hours` | `approval_escalation_due(db, company_id, created_at, now=...)` | Scheduled pending-approval escalation worker; caller must verify request is still pending and prevent duplicate escalation |
| `pos.allow_open_cash_drawer` | `cash_drawer_open_allowed(db, company_id, linked_to_transaction=...)` | POS cash-drawer command endpoint; deny transaction-free opening unless explicitly enabled |
| `integrations.auto_sync_enabled` | `automatic_sync_enabled(db, company_id)` and `integration_sync_due(...)` | Integration scheduler; must additionally check connection is active and enforce per-provider idempotency/locks |

## Safety and integration contract

- All reads use `get_company_setting`, so missing company overrides resolve to the registry's typed defaults.
- Unknown keys fail closed; no secrets or provider credentials are stored in company policy settings.
- These adapters do not perform external I/O, mutate business transactions, approve payroll, open physical drawers, or execute sync jobs themselves.
- Callers must check tenant/company authorization, current workflow status, permission to act, idempotency, and audit events before making side effects.
- A setting must remain classified as `catalog` until its owning workflow consumes the adapter and tests verify the end-to-end behavior.
- `general.date_format` is intended for date presentation only; it must not alter persisted dates, accounting dates, timezone conversion, or API machine formats.
