# PrimeERP — Stage 5 Financial / Inventory / Tenant Audit

Date: 2026-09-21
Base: 78bfdcd399b43c3211e8fafecd0a26c873c4bc83

## Migration audit correction

The first Stage 5 patch incorrectly treated `inventory_reservations.variant_id` as missing from the migration graph. A deeper migration-graph review found that the existing `20260914_variant_inventory_dimension` migration already adds `variant_id`, its foreign key, and its index to `inventory_reservations`.

The Stage 5 follow-up therefore **removed** the duplicate `20260921_reservation_variant_alignment` migration. This is the root-cause correction: the release graph must have one canonical owner for the schema change, not a second migration that fails with `DuplicateColumn` on a fresh database.

A regression contract test now verifies that the canonical `20260914_variant_inventory_dimension` migration declares the reservation variant dimension.

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

Inventory reservation routes validate that the requested company belongs to the current user’s tenant before invoking the service. Reservation service queries consistently scope by company_id and reservation mutations use company-scoped row locks.

Treasury list/events/transition operations are company-scoped as well.

The remaining release requirement is a full cross-module service-call audit to ensure internal callers cannot bypass the tenant boundary when they invoke company-scoped services directly.

## Reservation lifecycle

Reserve / release / consume / cancel are implemented with row locking and synchronized location + warehouse reserved balances.

Partial consumption is not silently emulated: the current domain model represents a reservation as one quantity and has no consumed-quantity ledger. A real partial-fulfillment implementation should therefore be a separate domain change with explicit quantities and accounting/inventory semantics, not a status-only patch.

## Release decision

Stage 5 correction completed:
- removed duplicate reservation variant migration;
- restored a single canonical migration owner;
- added a regression contract test for that canonical migration.

Stage 5 findings still open:
- exact Treasury → GL posting contract;
- complete cross-module tenant boundary audit;
- explicit partial-reservation/fulfillment ledger semantics.
