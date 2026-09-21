# PrimeERP — Stage 5 Financial / Inventory / Tenant Audit

Date: 2026-09-21
Base: 78bfdcd399b43c3211e8fafecd0a26c873c4bc83

## Root-cause fix implemented

### Inventory reservation schema/runtime drift
The reservation ORM/service already required `variant_id`, and reservation logic queried/created variant-aware balances, but the original `20260911_reservations` migration did not create `inventory_reservations.variant_id`.

This was a real release risk: a fresh database could successfully migrate the reservation table and then fail at runtime when the variant-aware service executed.

Stage 5 adds a forward-only Alembic migration:
`20260921_reservation_variant_alignment`

It adds:
- `inventory_reservations.variant_id`
- FK to `product_variants.id`
- index on `variant_id`

The frozen RC remains untouched.

## Treasury audit

Cheque lifecycle service was reviewed for:
- company scoping on reads and row locks;
- serialized status transitions;
- invalid transition rejection;
- event history;
- partner/company validation;
- reversal/withdrawal terminal states.

The lifecycle layer is present and row-locked. However, the dedicated accounting/checks and accounting/payments service files inspected in this branch are empty, so this audit does **not** claim that cheque state changes are fully connected to exactly-once GL posting. That remains an implementation gap rather than something to hide with a superficial patch.

## Tenant isolation audit

Inventory reservation routes validate that the requested company belongs to the current user's tenant before invoking the service. Reservation service queries consistently scope by company_id and reservation mutations use company-scoped row locks.

Treasury list/events/transition operations are company-scoped as well.

The remaining release requirement is a full cross-module service-call audit to ensure internal callers cannot bypass the tenant boundary when they invoke company-scoped services directly.

## Reservation lifecycle

Reserve / release / consume / cancel are implemented with row locking and synchronized location + warehouse reserved balances.

Partial consumption is not silently emulated: the current domain model represents a reservation as one quantity and has no consumed-quantity ledger. A real partial-fulfillment implementation should therefore be a separate domain change with explicit quantities and accounting/inventory semantics, not a status-only patch.

## Release decision

Stage 5 implementation finding fixed:
- migration/model mismatch for reservation variants.

Stage 5 findings still open:
- exact Treasury → GL posting contract;
- complete cross-module tenant boundary audit;
- explicit partial-reservation/fulfillment ledger semantics.
