# PrimeERP Master Execution Plan

PrimeERP is being developed as a production-grade modular ERP with a deliberate goal of exceeding Odoo-class breadth while adding stronger native capabilities in AI, tax compliance, treasury/collections, MENA localization, automation and integration reliability.

## Completion contract

A module is not considered complete because CRUD endpoints exist. A completed module must cover:

- domain model and database constraints
- migrations and rollback path
- tenant/company/branch isolation
- RBAC and authorization
- lifecycle/state transitions
- validation and idempotency
- accounting integration where financially relevant
- tax integration where taxable
- inventory/treasury/CRM/HR linkage where relevant
- audit trail
- API contract and error handling
- frontend workflows and empty/error/loading states
- reporting and drill-down
- automated tests
- production smoke checks
- observability and retry/DLQ behavior for integrations

## Product tracks

1. Core platform: tenancy, companies, branches, identity, RBAC, audit, settings, localization.
2. Finance: GL, AR, AP, cash, banks, reconciliation, periods, budgets, assets, accruals, FX and financial statements.
3. Commercial: CRM, sales, purchasing, pricing, promotions, commissions and contracts.
4. Inventory: catalog, variants, UOM, warehouses, reservations, transfers, valuation, FIFO/average cost, lots/serials and landed cost.
5. Operations: manufacturing, POS, restaurant, service, projects and subscriptions.
6. Treasury: cheques, under-collection, deposited, returned, resubmitted, replacement, reversals, refunds and collection plans.
7. Tax compliance: VAT/WHT/other taxes, effective-dated rules, tax snapshots, reconciliation, return drafts and ETA e-invoice/e-receipt integration.
8. Logistics: carriers, rates, shipments, COD, settlement and returns.
9. Integrations: REST API, webhooks, event processing, retries, idempotency, Salla, payment/shipping/banking connectors.
10. SaaS: plans, modules, entitlements, trials, billing, expiry and platform administration.
11. Reporting: report registry, parameterized reports, exports, dashboards, scheduled delivery and delivery history.
12. AI: financial/operational performance analysis, anomaly detection, forecasting, tax audit assistance, natural-language reporting and recommendations.

## Current execution in this release

- ETA e-invoice module is wired into the API and now has database-level idempotency for source/submission/document identifiers.
- Report delivery models are registered with Alembic metadata.
- Secure report preview/delivery APIs support email and WhatsApp provider delivery when configured.
- Durable report schedules and delivery metadata are persisted.
- AI analysis endpoint provides deterministic control checks and an optional OpenAI-compatible provider with a safe fallback when the provider is unavailable.
- Tax-return draft model and calculation/reconciliation workflow are persisted.
- PostgreSQL driver dependency is aligned with the application's Psycopg 3 configuration.
- HTTP integration dependency is explicitly declared.

## Egyptian Tax Authority boundary

PrimeERP must distinguish:

- ETA e-invoice/e-receipt document submission APIs: automatable through the official integration surface.
- Tax-return filing: only automate final submission for a return type when ETA provides and authorizes the corresponding submission API. Otherwise PrimeERP produces a validated, reconciled filing package and tracks the filing state without pretending that portal submission occurred.

## Release gates

Every implementation batch must pass:

1. Python compile/import smoke.
2. Alembic head and upgrade validation.
3. PostgreSQL migration test.
4. API security boundary test.
5. Tenant-isolation tests.
6. Lifecycle/idempotency tests.
7. Module entitlement tests.
8. Frontend build/type checks.
9. Integration contract tests with mocked providers.
10. Full release gate before production merge.

Local Docker being unavailable must never be treated as proof that the code is correct or incorrect; CI must provide an isolated PostgreSQL validation path.
