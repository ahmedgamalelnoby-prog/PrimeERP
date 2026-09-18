# PrimeERP Module Development Standard

## Goal

Every module must be independently understandable, testable and replaceable without changing unrelated modules.

## Backend module boundary

Use this shape where the module has business logic:

- `api/router.py` — HTTP routes and request/response wiring only.
- `schemas/` — Pydantic contracts.
- `models/` — SQLAlchemy persistence models.
- `service.py` or `services/` — business rules and transactions.
- `repositories/` — reusable data access when queries become non-trivial.
- `tests/` — unit and integration coverage.
- `alembic/versions/` — one focused migration per change; merge heads explicitly.

Rules:

1. Routers must not contain complex business rules.
2. Tenant/company authorization is mandatory for tenant data.
3. Never use a hard-coded company ID.
4. Cross-module calls must go through a service/API contract, not private implementation details.
5. State transitions must be explicit and validated server-side.
6. Reversible financial operations must create an auditable reversal/event.
7. Every new database field needs ORM + migration + validation coverage.

## Frontend module boundary

Use:

- `pages/` — route-level screens.
- `components/` — module-local UI.
- `services/` — module API calls when more than one page uses them.
- `hooks/` — module data/state behavior.
- `schemas/` — client validation.
- `types/` — module contracts.

Shared UI and API infrastructure belongs under `frontend/src/shared`, never copied into individual modules.

## API and UX rules

- Use the active company/tenant context; never silently fall back to company 1.
- Prefer server-side filtering, pagination and validation.
- Loading, empty, error and success states are required.
- Destructive actions require confirmation.
- Lists must expose search/filter/sort where the dataset can grow.
- Forms must use human-readable selectors instead of raw database IDs whenever a lookup endpoint exists.
- Arabic and English labels must remain aligned.

## AI rules

All AI features must:

1. Use the configured `AI_MODEL`; never hard-code a provider model in a page.
2. Receive current product/module knowledge from the versioned Module Registry.
3. Ground business analysis in live ERP data when such data exists.
4. Never invent transactions, permissions, prices, legal requirements or unavailable features.
5. Return deterministic rule-based fallback results when practical.
6. Never request passwords, tokens, API keys or secrets.
7. Expose a knowledge version so support teams can identify which product context produced an answer.
8. Keep prompts and model settings configurable through environment-backed settings.

## Update workflow

For a module change:

1. Change the module implementation.
2. Add/adjust tests.
3. Add the migration if the schema changes.
4. Update the Module Registry when capabilities or status change.
5. Update navigation/catalog metadata if the user-facing surface changes.
6. Run module tests.
7. Run the complete Release Gate before release.

The Module Registry is the single source of truth for product-facing module metadata. Frontend catalog and AI product context should consume it instead of maintaining separate copies.
