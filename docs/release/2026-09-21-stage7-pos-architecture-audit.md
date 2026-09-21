# PrimeERP — Stage 7 POS Domain Architecture Audit

Date: 2026-09-21
Baseline: 95e93e563f87b95d14aa7f684e6b09414b463d87
Branch: audit/2026-09-21-stage7-pos-domain

## Release safety

The frozen RC branch remains untouched. This stage is an audit only; no production POS implementation is being invented before its dependencies and accounting contracts are mapped.

## Finding 1 — POS is not a registered API domain

The v1 API router registers accounting, inventory, catalog, commerce, shipping, treasury, integrations, SaaS, and related domains, but there is no POS router registration.

Therefore POS cannot currently be treated as an end-to-end runtime module.

## Finding 2 — Existing primitives are available

The repository already contains reusable building blocks needed by a POS implementation:

- Catalog menus and menu items.
- Product price lists and product prices.
- Recipes and recipe lines.
- Inventory items, variants, stocks and stock moves.
- UOM and conversion infrastructure.
- Commerce sales documents and payments.
- Canonical JournalService / Commerce Accounting.
- Tenant/company/branch boundaries.
- Inventory reservation infrastructure.

The correct implementation should reuse these contracts instead of creating parallel product, pricing, inventory or accounting engines.

## Finding 3 — Required POS aggregate

The POS domain should be implemented as a bounded orchestration layer around existing primitives:

Outlet → POS Device → Cashier/Session → Order → Order Lines → Payment(s) → Inventory/Recipe consumption → Accounting → End-of-Day close.

Required state invariants:

1. An outlet, device, cashier and session must belong to the same tenant/company/branch scope.
2. A device cannot be active in two open sessions simultaneously.
3. A cashier cannot post against another company's outlet/session.
4. A posted/finalized order is immutable except through explicit reversal/return workflows.
5. Payment totals cannot exceed the payable order balance unless an explicit overpayment policy exists.
6. Duplicate payment requests must be idempotent.
7. Stock consumption must be source-identified and exactly-once.
8. Recipe/UOM consumption must be based on the finalized sold quantity.
9. Accounting must use the canonical JournalService and source identity.
10. End-of-day close must lock the session and prevent later ordinary postings.

## Finding 4 — Inventory/recipe integration contract

For stockable menu products with recipes, the POS sale should resolve the active recipe version and create inventory consumption using existing inventory stock-move/valuation infrastructure.

The implementation must not introduce a second reservation or valuation algorithm.

Partial/return behavior must remain explicit. A return should reverse the original business effect rather than mutate a delivered/final state.

## Finding 5 — Accounting contract

POS should not write journal rows directly.

It must use the existing canonical accounting path and configurable company accounts. Payment methods need explicit account mapping and source identity so the same POS order/payment cannot post twice.

## Stage 7 implementation boundary

The next implementation wave should add:

- POS models for outlet/device/cashier/session/order/order-line/payment/EOD close.
- Tenant/company/branch constraints.
- Canonical state transitions and idempotency.
- Menu/price/recipe/UOM resolution.
- Inventory consumption orchestration.
- Payment and accounting integration through existing services.
- API schemas/router and module entitlement.
- Alembic migration.
- Focused contract tests covering the complete sale lifecycle and close/reversal paths.

No production POS code is added in this audit because the module does not currently exist in the API tree and speculative implementation would create duplicate business contracts.

## Remaining release gaps after this audit

1. POS domain implementation and end-to-end trace.
2. Explicit partial reservation ledger semantics.
3. Full cross-module tenant boundary audit.
4. Subscription lifecycle proof: Plan → Subscription → Renewal → Billing/Payment → Expiry/Lock → Entitlement.
5. Final combined release gate after all implementation waves.
