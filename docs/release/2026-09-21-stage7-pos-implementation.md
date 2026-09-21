# Stage 7 POS Implementation

Baseline: `95e93e563f87b95d14aa7f684e6b09414b463d87`
Branch: `audit/2026-09-21-stage7-pos-domain`

Implemented:
- POS outlet with branch and inventory-location binding.
- POS device and one-open-session-per-device invariant.
- POS cashier session lifecycle and EOD close guard.
- POS orders and immutable finalized state contract.
- Menu/product/recipe-aware order lines using existing Catalog recipes.
- Recipe ingredient consumption through the existing InventoryStockMoveService.
- Direct item consumption when no recipe exists.
- Source identity/idempotency for POS inventory movements.
- POS sale accounting through canonical JournalService using Commerce accounting configuration.
- POS payment accounting as AR settlement through canonical JournalService.
- Payment idempotency and outstanding-balance protection.
- Tenant/company checks on every service entry point.
- API registration under the existing sales entitlement boundary.
- Alembic migration `20260921_pos_domain`.
- Contract tests.

Safety:
- Frozen RC was not modified.
- Existing inventory, accounting, commerce, recipe and UOM engines are reused; no parallel valuation or GL engine was introduced.

Known boundary:
- Payment-method-specific GL accounts currently use the existing Commerce default payment account. A future treasury/payment-method mapping can replace this without changing the POS aggregate.
- Partial reservation ledger semantics remain a separate release gap.
- Final release gate is required before promotion.
