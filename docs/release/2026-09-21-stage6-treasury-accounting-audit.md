# PrimeERP — Stage 6 Treasury / Accounting / Tenant Audit

Date: 2026-09-21
Base: 8041c4e9ec30f078e8ec6d1bfd1f2ffd2fb2bde0

## Release verification

- Runtime Release Gate #51 on the Stage 5 correction head succeeded.
- Self-Hosted Release Gate #2342 was cancelled immediately after creation and had no jobs; it is not treated as a product failure and was not blindly rerun.
- Frozen RC remains untouched.

## Root-cause audit

### Accounting engine

The repository does contain a real accounting posting path. Commerce Accounting calls the canonical JournalService, which:
- validates tenant/company/branch ownership;
- requires an open posting period;
- validates active account combinations;
- validates balanced debit/credit lines;
- records source module/entity/id;
- uses the database source idempotency guard;
- locks the journal entry and posting period during lifecycle mutations;
- supports atomic journal reversal.

Therefore the earlier statement that all accounting posting infrastructure was empty was too broad. The empty `accounting/checks`, `accounting/payments`, and legacy `journal_entries` paths are not the canonical posting engine.

### Treasury gap

Treasury cheque transitions currently update `treasury_cheques` and append `treasury_cheque_events`, with company-scoped row locking and transition validation. They do not invoke the canonical JournalService.

This means the critical invariant is still open: a cheque transition that has an accounting consequence is not yet proven to create exactly one corresponding journal entry, nor is the accounting mapping for every transition explicitly configured.

No speculative debit/credit mapping was added in this stage because returned/deposited/collection/issued-cheque accounting can differ by configured bank, clearing, receivable, payable, and returned-cheque accounts.

### Commerce payment lifecycle

Commerce payments already have company-scoped idempotency keys. Commerce Accounting posts the payment using a traceable source and the canonical JournalService. Reversal creates a separate accounting source identity and reverses the original lines when the original journal exists.

### Period lock

The canonical JournalService checks the posting period both while creating the draft context and again under row lock before posting/reversing. This is the required protection against posting into a closed period.

### Tenant isolation

The canonical accounting path requires tenant_id + company_id and verifies branch, fiscal period, journal, and accounts against the same tenant/company boundary. Treasury transitions lock by cheque id plus company_id.

The remaining cross-module requirement is to add a treasury-to-accounting integration boundary that receives an already-authorized company/tenant context and refuses mismatched objects before posting.

## Stage 6 decision

The audit found a concrete architectural gap but did not hide it with a superficial patch:

- Canonical accounting engine: present and hardened.
- Commerce → Accounting: present with source idempotency and period guards.
- Treasury → Accounting: **not integrated yet**.
- Tenant boundary: strong in the inspected canonical accounting path; cross-module treasury posting contract remains open.
- No Alembic migration was added in Stage 6 because the correct Treasury accounting configuration schema has not yet been established.

Next implementation is a dedicated Treasury Accounting Integration domain, with explicit company-level account mapping and exact-once source identity per cheque accounting event, followed by full transition coverage and release verification.
