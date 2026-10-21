# PrimeERP Phase 2 — Dependency Map / Cross-Module Audit / Batch Fix

Status: implementation-complete baseline; validation is intentionally deferred to the Release Gate.

## Closed in this phase
- Central SQLAlchemy model registry repaired and expanded for Sales, Purchasing, POS, Treasury and Shipping.
- Sales invoices, purchase invoices and treasury source documents are connected to accounting journal posting.
- Source-document journal posting is atomic and enforces balanced positive entries.
- Treasury transfer journal linkage is persisted.
- Treasury account GL linkage is persisted by migration.
- Treasury cheque lifecycle transitions are guarded.
- Shipping carrier rules now have a calculation endpoint supporting fixed, percentage, per-kg, per-item, zone, COD and Visa/card fees.
- Tenant/company/branch scope checks are retained across the newly integrated flows.
- Inventory movement supports transactional callers through commit=False.

## Integrated dependency chain
Master Data → Inventory → Sales → Fulfillment → Sales Invoice → Purchasing → POS → Treasury → Shipping → Accounting.

## Validation policy
No isolated test/rerun loop is used during this batch. The complete backend compile, migration graph/upgrade, frontend build, database integrity, tenant-isolation and runtime checks belong to the final Release Gate after the remaining functional waves are implemented.
