# PrimeERP company-policy wiring status

Last reviewed: 2026-10-22

This document distinguishes a setting being editable in the company settings screen from a setting being enforced by a production workflow. A consumer helper or a frontend local-storage preference alone is not sufficient evidence to mark a policy as runtime-enforced.

## Runtime wiring currently verified in code

- `integrations.auto_sync_enabled`: consumed by the automatic Salla integration worker. The worker polls active Salla connections and checks company policy before claiming work. Default remains disabled, so existing tenants are not silently opted into automatic external API traffic.
- Inventory stock issue: batch/serial/expiry checks now read tracking flags with backward-compatible defaults for older test fixtures that do not expose those fields. This is a compatibility fix, not proof that company-level batch/serial defaults are enforced in every inventory workflow.
- The company settings API validates keys and typed values, scopes reads/writes to the active company in the current tenant, and records audit events for changed settings.

## Settings that must remain catalog-only

These policies have helper functions, but the owning workflow is not implemented or not yet connected end-to-end. Do not present them as enforced:

- `general.date_format`: the settings page stores a browser-local preference and a formatter exists, but repository search has not verified that business screens consistently use the formatter.
- `hr.attendance_source`: the existing monolithic HR attendance service enforces the selected source by blocking manual writes unless the configured source is `manual`. The service now calls the shared company-policy consumer helper, and a focused regression test covers the non-manual values. Dedicated nested attendance files remain placeholders; biometric/mobile/integration ingestion is not implemented, so the setting remains catalog-only.
- `hr.biometric_sync_interval_minutes`: no biometric-device polling worker or complete attendance ingestion workflow is present.
- `hr.payroll_requires_approval`: HR payroll API/service/router files are empty placeholders.
- `workflow.approval_mode` and `workflow.escalation_after_hours`: consumer helpers exist, but the operations approvals module's model/schema/service/router files are empty placeholders; there is no durable approval lifecycle consuming the plan or escalation deadline.
- `pos.allow_open_cash_drawer`: a policy helper exists, but no standalone cash-drawer open endpoint/command is present. Opening a cashier shift and declaring opening float is not equivalent to opening the physical cash drawer, so this setting must not be applied to shift opening.

## Verified HR policy wiring

- `hr.require_attendance_approval` is consumed by the existing attendance-correction workflow: corrections remain pending until an authorized decision when enabled, and are applied immediately when disabled.
- `hr.attendance_source` is consumed by the actual manual attendance creation service through the shared policy adapter. A regression test covers biometric/mobile/integration selections being unable to write through the manual endpoint. The non-manual connectors still need to be implemented before promoting the setting to runtime.

## Required implementation before promoting these settings

1. Implement and migrate durable HR attendance/punch, biometric device configuration/sync cursor, payroll run, and approval request/step records with tenant/company scoping.
2. Enforce source restrictions at the actual attendance ingestion endpoint; schedule biometric polling using the configured interval and idempotent external event IDs.
3. Block payroll finalization/payment until required approvals are complete; make approval mode deterministic and escalation operate only on pending requests.
4. Add an explicit audited cash-drawer command and enforce the policy there; do not infer a drawer command from shift opening.
5. Route date rendering through one company-aware formatter across business screens and test all supported formats.
6. Add focused service/API tests and migration checks, then change catalog status only after the complete path is covered.

## CI status at review time

The latest workflow run for the current branch was still queued/in progress when checked. The preceding completed run had two registry assertion failures because `integrations.auto_sync_enabled` had moved to runtime while the expectations still listed it as catalog-only. Those expectations have been corrected, but the subsequent CI result must be checked before claiming a green build.
