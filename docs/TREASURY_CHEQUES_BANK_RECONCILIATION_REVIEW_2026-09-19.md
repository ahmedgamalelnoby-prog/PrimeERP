# Treasury & Cheque Control Review — 2026-09-19

## Verified backend surface
- Company/tenant isolation is enforced at the Treasury router.
- Cheque lifecycle is explicit and event-audited.
- Received flow: received -> deposited -> under_collection -> collected, with returned/resubmitted paths.
- Issued flow: issued -> cleared/reversed.
- Withdrawal is date-controlled and exposed through a dedicated withdrawable endpoint.
- Terminal states cannot transition further.
- Partner ownership is validated on cheque creation.

## Frontend corrections
- Treasury UI is connected to the existing Treasury API.
- Entry validation prevents invalid zero/blank cheque submissions.
- UI actions mirror the backend lifecycle.

## Bank reconciliation status
PrimeERP does not currently expose a verified bank-statement import/matching/reconciliation module in the reviewed backend surface. This is therefore a genuine next implementation wave, not treated as complete merely because Treasury/Cheques exist.

## Required next wave
1. Bank accounts and statement lines.
2. Statement import with duplicate detection.
3. Matching rules: exact reference, amount/date tolerance, cheque number, partner.
4. Manual match/unmatch queue.
5. Bank fees and transfers.
6. Reconciliation session: open -> matching -> balanced -> closed.
7. Accounting journal linkage and immutable audit trail.
8. Tenant/company/branch scope and permissions.
9. Idempotent import and replay-safe matching.
10. Integration tests for duplicate imports, partial matches, reversal and close controls.
