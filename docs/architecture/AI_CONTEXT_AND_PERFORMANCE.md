# PrimeERP AI Context & Performance Foundation

## Objectives
- Keep AI project awareness current as the codebase evolves.
- Prevent AI context from depending on one long conversation.
- Keep modules independently deployable and avoid synchronous cross-module coupling.
- Make normal user commands fast by default and move expensive work to background jobs.

## AI context contract
Every material release/change should update a machine-readable project snapshot containing:
- current release/branch
- latest commit SHA
- module inventory and ownership
- API contracts and schema version
- database/Alembic head
- enabled integrations
- known open defects and blocked areas
- latest verified test/release-gate status
- architecture decisions
- last successful deployment/migration
- compatibility/deprecation notes

The AI assistant must treat this snapshot as the source of current project state, not as a replacement for source-code inspection. Before making implementation claims it should refresh the snapshot and inspect the affected module/contracts.

## Module boundaries
- Modules communicate through explicit service interfaces and stable API/domain contracts.
- Avoid importing another module's router, ORM internals, or private helpers.
- Cross-module workflows belong in application/domain services.
- Events are preferred for non-critical side effects.
- Database transactions remain authoritative for financial/inventory state.

## Performance rules
- No unbounded list queries.
- Pagination/filtering is mandatory for large collections.
- Add indexes from measured query plans, not speculation.
- Avoid N+1 ORM access; use eager loading only where measured.
- Do not perform external API calls inside user-facing database transactions.
- Expensive reports, exports, AI retrieval, sync and reconciliation run asynchronously.
- Cache only data with a defined invalidation/version policy.
- Frontend should use request deduplication, cancellation, pagination and lazy module loading.
- API responses should return only required fields for list views.

## Reliability
- Every write path must have explicit transaction boundaries.
- Retries must be idempotent.
- Background jobs require retry/backoff and a dead-letter/error state.
- Tenant/company authorization is enforced at the service/data boundary, not only in the UI.
- Observability must cover latency, error rate, queue depth and slow queries.

## Development gate
Before merging a platform change:
1. static/architecture checks
2. backend unit/integration tests
3. migration graph validation
4. frontend type/build checks
5. performance smoke tests for affected endpoints
6. Docker startup/health
7. tenant-isolation checks
8. release-gate regression suite

Do not claim production readiness while a required gate is unverified.
