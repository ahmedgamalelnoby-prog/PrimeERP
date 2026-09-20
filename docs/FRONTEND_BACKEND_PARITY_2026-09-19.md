# PrimeERP Frontend / Backend Parity — 2026-09-19

## Objective

PrimeERP uses the backend as the source of business rules and the frontend as
the complete operator experience. A module is considered integrated only when
its API contracts, permissions, tenant/company scope, lifecycle, validation,
errors and UI are connected.

## Parity policy

- Every backend business module must have a corresponding frontend module unless
  it is explicitly infrastructure-only.
- Every frontend business module must have a backend namespace unless it is
  explicitly presentation-only/public.
- Frontend API calls must use the shared authenticated client.
- Navigation routes must resolve to real frontend routes.
- Critical backend contracts are checked by CI.
- Backend/frontend parity is structural; functional completion still requires
  end-to-end tests for each business workflow.

## CI guard

`backend/scripts/check_frontend_backend_alignment.py` now checks both the
existing critical API contracts and module-level parity. Explicit exceptions
are documented in the script because some frontend entries are UI shells or
backend infrastructure namespaces.

## Completion rule

For each module, close the chain:

UI -> API client -> FastAPI route -> permission/scope -> service/domain rules
-> database -> accounting/inventory side effects -> audit/idempotency
-> API response -> UI state/error handling.

Adding a page without this chain is not considered integration.
