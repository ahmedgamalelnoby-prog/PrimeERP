# PrimeERP — Stage 3 Batch Fix / Cross-module Business Invariant Hardening
Date: 2026-09-21
Baseline: dfc677fda5721b2c19e22af3a7217cbfe4cac221
Frozen RC: release/2026-09-21-rc1
Fix branch: fix/2026-09-21-business-invariants

## Implemented root-cause fixes

### Shipping state machine
- Removed the duplicate shipment transition table from the API router.
- Centralized shipment transitions in `app.modules.shipping.service`.
- Made `delivered` a terminal state. A delivered shipment cannot be reopened as `returned`; returns must use the dedicated return workflow.
- Kept the existing normal path pending -> picked_up -> in_transit -> out_for_delivery -> delivered.
- Added a regression test proving delivered is terminal.

### Shipping fee invariant
- Removed duplicated COD fee arithmetic from the router.
- The router now uses the shared `calculate_shipping_fee` domain function, preserving one rounding and validation rule.
- This prevents API/service drift between configured carrier pricing and shipment creation.

### SaaS subscription mutation concurrency
- The active subscription lookup used by lifecycle mutations now uses a row lock (`SELECT ... FOR UPDATE`).
- This serializes concurrent conversion/renewal/cancellation mutations against the same active subscription and prevents stale-state mutation during a transaction.

## Explicitly not changed
- Frozen RC branch remains untouched.
- No Alembic migration was introduced in this wave.
- Treasury/accounting posting integration was not invented or approximated without a verified accounting posting contract.
- Inventory reservation, POS accounting, and Salla finalization were not modified blindly; their concrete service contracts must be traced before changing them.

## Next verification
Before any merge toward RC:
1. Static/architecture checks.
2. Targeted business invariant tests.
3. Migration graph audit.
4. Full Release Gate.
5. Compare final fix branch against the frozen RC and verify only intentional changes remain.
