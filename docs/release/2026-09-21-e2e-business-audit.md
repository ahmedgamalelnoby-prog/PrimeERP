# PrimeERP — End-to-End Business Audit
Date: 2026-09-21
Baseline: dfc677fda5721b2c19e22af3a7217cbfe4cac221
Release candidate: release/2026-09-21-rc1

## Scope
Business-flow review before any new CI: Accounting, Commerce/Sales, Payments/Treasury/Cheques, Inventory/Reservations, Shipping/Salla, POS, SaaS/Entitlements, Identity/Tenant boundaries, Integrations.

## Verified structural controls
- Treasury cheque transitions are explicit and row-locked with company scoping.
- Treasury routes enforce permission + SaaS module entitlement + tenant/company ownership.
- Commerce accounting posting validates double-entry, source identity, open posting period, fiscal year, company and tenant context, and uses idempotent source lookup.
- Salla integration has signed public webhooks, payload-size limits, external-event idempotency, connection/company scoping, and processing/finalization paths.
- Integration product mappings have uniqueness constraints for external identity and local product/variant identity.
- SaaS has explicit lifecycle/entitlement components and module guards are wired into protected routers.
- The RC branch is frozen on the same commit as the 5/5 green release gates.

## Findings requiring the next implementation wave
### 1. Subscription lifecycle surface
The top-level subscriptions service, CRUD, permissions, models and router files are empty while functionality is split into nested billing/memberships/plans/renewals packages. This is not automatically wrong, but it requires an end-to-end contract check proving that plan creation -> subscription -> renewal -> billing/payment -> expiry/lock -> entitlement enforcement is actually reachable through registered API routes and frontend flows.

### 2. Treasury-to-accounting integration
Cheque state transitions and event history are present, but the inspected treasury service is primarily a state/event layer. A release-level business audit must verify that deposit/collection/return/reversal/withdrawal actions create exactly the intended accounting/treasury ledger effects and cannot double-post.

### 3. Commerce accounting completeness
Sales invoice and credit-note posting paths are present with double-entry and source idempotency. The same invariant must be traced across purchase receipts/bills, inventory valuation, payments/allocations, returns, and period close so every operational posting has one accounting source-of-truth.

### 4. Inventory reservation lifecycle
Inventory contains dedicated reservation/stock-move areas, but the business audit must trace reserve -> consume -> release -> partial fulfillment -> cancellation -> return and verify row-lock/idempotency behavior across Sales, Commerce, Shipping and POS.

### 5. Shipping/Salla finalization
Salla webhook processing and shipment synchronization are wired. The audit must verify the complete state chain: order import -> mapping -> ERP order -> reservation -> packing/shipping -> delivered/returned -> final accounting impact, including duplicate/replayed webhook safety.

### 6. POS accounting and stock impact
POS has separate orders, payments, devices and cashier areas. The release flow still needs a single traced scenario proving outlet/device/cashier selection, payment allocation, stock consumption, recipe/UOM handling where applicable, posting, and end-of-day/period behavior.

### 7. Tenant isolation across cross-module writes
Protected routers consistently use company/tenant checks in the inspected areas. Cross-module service calls still need an audit for cases where a service receives only company_id or an object id and performs secondary queries without tenant scoping.

## Release decision for this stage
This audit is recorded as **AUDIT COMPLETE — IMPLEMENTATION FINDINGS OPEN**.
No changes were applied to the frozen RC branch. The findings are intentionally carried to the batch-fix stage so the RC remains immutable.

## Required next wave
Batch-fix the above business invariants and add/strengthen end-to-end coverage before running another full Release Gate.
