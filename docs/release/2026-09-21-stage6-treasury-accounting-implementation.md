# Stage 6 — Treasury → Accounting Integration

## Root cause
Treasury cheque state transitions were tenant/company scoped and row-locked, but they only persisted treasury state/events. They did not call the canonical Accounting JournalService, so deposit, collection, return, reversal, withdrawal and cheque issuance/clearing had no exact-once GL boundary.

## Implementation
- Added TreasuryAccountingSettings, scoped one-to-one per company.
- Added tenant-scoped configuration endpoint for journal, branch, bank and cheque lifecycle accounts.
- Added TreasuryAccountingService as the single cheque-event → journal adapter.
- Every accounting journal uses source identity treasury / cheque_event / event.id for retry-safe idempotency.
- Accounting remains atomic with the treasury transition: if journal validation, account mapping or open-period validation fails, the transaction rolls back and the cheque state is not committed.
- Reused the canonical JournalService for company/tenant account validation, balanced entries, period locks, approval and posting.
- Relaxed the journal manual-entry guard only for non-null integration sources; manual entries remain blocked when the journal disallows them.

## Lifecycle coverage
Received cheques: created → deposited → under collection → collected.
Returned flow: returned → resubmitted.
Issued cheques: created → cleared.
Terminal corrections: withdrawal and reversal use the configured lifecycle account corresponding to the prior financial state.

## Configuration safety
No account IDs are hardcoded. The company must explicitly configure all treasury accounts, journal and branch. Configuration writes verify company/tenant ownership and active accounts.

## Release safety
The frozen release/2026-09-21-rc1 branch is untouched. This implementation remains isolated on the Stage 6 branch until its migration, static, runtime and full Release Gate checks are green.
