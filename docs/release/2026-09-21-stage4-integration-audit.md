# PrimeERP — Stage 4 Integration Invariant Hardening
Date: 2026-09-21
Baseline: d3d520719d354c3d6706552b2e0a307f87ae994c
Branch: fix/2026-09-21-integration-invariants

## Implemented root-cause fix

### Salla → Shipping terminal-state consistency
The Salla shipment adapter previously had its own terminal-state behavior and could change an ERP shipment from `delivered` to `returned`. That bypassed the Stage 3 ERP shipping invariant that `delivered` is terminal.

The adapter now:
- Reuses the canonical ERP `SHIPMENT_TRANSITIONS` contract.
- Preserves `delivered` when a later Salla `returned` or `cancelled` event arrives.
- Leaves inventory restoration/accounting reversal to the dedicated Salla return workflow.
- Rejects impossible terminal transitions instead of silently mutating the shipment.

Regression coverage was added for delivered→returned, delivered→cancelled, valid out_for_delivery→returned, and invalid pending→returned.

## Deep-audit findings retained for the next batch

### POS
The top-level POS module files (`models.py`, `router.py`, `service.py`, `schemas.py`) and the inspected orders/payments/session/cashier service files are currently empty. The module is therefore not yet an end-to-end accounting/inventory POS implementation, even though SaaS module catalog entries expose POS.

No speculative POS implementation was added in this wave; the correct next step is a dedicated POS domain build/trace with outlet/device/cashier/payment/recipe/UOM/stock/EOD contracts.

### Treasury → Accounting
Cheque lifecycle locking and event history exist, but the inspected treasury service currently handles state transitions/events and does not itself prove that deposit, collection, return, reversal, and withdrawal each generate exactly-once accounting postings. This remains an explicit release-audit item until the accounting posting contract is traced end-to-end.

## RC safety
The frozen RC branch remains untouched. This branch contains only the Salla shipping invariant hardening and its regression coverage plus this audit note.
