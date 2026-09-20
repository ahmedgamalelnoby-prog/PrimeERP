# PrimeERP Bank Reconciliation — 2026-09-19

Implemented operational bank reconciliation on top of the existing Treasury and Accounting boundaries.

## Backend
- Bank accounts scoped by company/tenant.
- Bank statements with immutable closed state.
- Statement lines with deterministic SHA-256 fingerprint for replay-safe imports.
- Duplicate line detection per statement.
- Debit/credit validation.
- Reconciliation sessions with book balance, bank balance and difference.
- Automatic matching by payment reference + amount, then cheque number + amount.
- Manual matching to Commerce Payment or Treasury Cheque.
- Partial matching and unmatching.
- Direction controls: sales/received sources match bank credits; purchases/issued sources match bank debits.
- Close is allowed only when balances are equal and all statement lines are fully matched.
- Closed statements/reconciliations are immutable.
- Company/tenant isolation and existing Treasury permissions are reused.

## Frontend
- `/treasury/reconciliation`
- Bank account creation/listing.
- Statement creation/listing.
- Statement line entry.
- Automatic matching.
- Manual matching.
- Reconciliation status and close control.

## Accounting boundary
Bank accounts can reference an existing account combination. The implementation does not create a duplicate ledger. Journal/fee adjustments remain a separate posting operation and must use the existing accounting posting engine.

## Remaining hardening
- CSV/OFX/MT940 import adapter.
- Source candidate search endpoint for richer manual matching.
- Bank fee/transfer adjustment posting through the existing posting engine.
- Full API/E2E tests against PostgreSQL and migration-upgrade validation.
