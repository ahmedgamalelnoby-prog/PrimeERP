# PrimeERP Frontend ↔ Backend Endpoint Matrix — 2026-09-19

This matrix is intentionally based on executable contracts, not directory/file presence.

## Connected operational slices

| Business slice | Backend contract | Frontend surface | Status |
|---|---|---|---|
| Product catalog | `/catalog/categories`, `/catalog/price-lists`, `/catalog/recipes`, `/catalog/pricing-impact` | `modules/products/pages/ProductsPage.tsx` + `products.api.ts` + `/products` route | Connected |
| Treasury cheques | `/treasury/cheques` + lifecycle actions | `modules/treasury/pages/TreasuryPage.tsx` + `/treasury/*` | Connected |
| Accounting journals | `/accounting/journal-entries/*` and journal services | Accounting pages + shared posting invariants | Connected at API/domain layer; E2E coverage still required |
| Inventory moves/transfers | dedicated stock-move/transfer routers | Inventory transaction/transfer pages | Connected contract surface; E2E coverage still required |
| Salla/Shipping | Salla public app + shipping routers | Shipping pages + Salla embedded surface | Connected contract surface; regression suite exists |

## Important correction

The old UI used the inventory landing page for `/products`. That was a navigation-level match, but not a functional product-catalog integration. It is now a dedicated Products screen that consumes the existing Catalog API.

The backend `catalog` namespace is explicitly mapped to the frontend `products` namespace in the parity guard.

## Definition of connected

A screen is considered connected only when it:
1. uses the shared authenticated API client;
2. sends the company/tenant scope required by the backend;
3. handles loading and API errors;
4. renders data returned by the actual endpoint;
5. is reachable from the application router/navigation;
6. is covered by the parity guard.

A future endpoint is not marked connected merely because a route or placeholder page exists.

## Remaining work

The next parity waves must replace generic `OperationalPage`/workbench placeholders with domain screens where the backend already exposes real contracts, and must add missing backend APIs where the frontend represents a genuine business capability without a server-side contract.

Priority:
1. Sales order/invoice flow
2. Purchasing order/bill flow
3. Inventory item/warehouse operations
4. AR/AP and reconciliation
5. Manufacturing/recipe execution
6. POS/restaurant
7. CRM
8. HR/payroll
9. Reports/drill-down
10. Integration Hub and Salla synchronization

Each wave must include API + UI + permission/scope + lifecycle + accounting/inventory side effects + audit/idempotency + tests.
