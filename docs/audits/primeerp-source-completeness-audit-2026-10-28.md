# PrimeERP source completeness audit — 2026-10-28

## Scope and method
This is a static Git tree audit of branch `feature/primeerp-completion-visibility-20261028`. It counts tracked files with zero bytes; this is a strong scaffold signal, not by itself proof that the business capability is absent elsewhere in the repository. The counts below are scoped to the listed module directories only.

## Findings

| Module directory | Tracked files | Zero-byte files | Non-empty files |
|---|---:|---:|---:|
| `backend/app/modules/accounting/` | 312 | 245 | 67 |
| `backend/app/modules/sales/` | 47 | 42 | 5 |
| `backend/app/modules/inventory/` | 194 | 122 | 72 |
| `backend/app/modules/purchases/` | 0 | 0 | 0 |

The purchases path does not exist under `backend/app/modules/purchases/` on this branch. Before implementation, confirm whether purchasing is implemented under another module path rather than assuming it is absent from the whole system.

At least **89 zero-byte files** in Sales and Inventory have core implementation names such as `router.py`, `service.py`, `models.py`, `schemas.py`, `repository.py`, or `api.py`. Examples include:
- Sales invoices: `backend/app/modules/sales/invoices/{models.py,router.py,schemas.py,service.py}`
- Sales orders: `backend/app/modules/sales/sales_orders/{models.py,router.py,schemas.py,service.py}`
- Inventory stock: `backend/app/modules/inventory/stock/{models.py,router.py,schemas.py,service.py,repository.py}`
- Inventory transfers, recipes, waste, barcode, and categories have similar zero-byte core files.

Accounting also contains many zero-byte submodule files. However, a separate accounting reports implementation exists at `backend/app/modules/accounting/reports/`; do not infer that all accounting capabilities are missing solely from this directory count.

## Priority and release implications
1. **P0 — avoid false completion claims:** keep Sales invoice/order and Inventory stock/transfer/adjustment workflows marked in progress until their real API, persistence, authorization, and lifecycle tests are verified.
2. **P1 — locate canonical purchasing implementation:** search module registration and router mounting for purchasing/procurement paths, then audit that actual implementation.
3. **P1 — select one vertical slice at a time:** implement and test invoice lifecycle (draft → validated/posted → reversal/credit note), including company isolation, totals/tax validation, idempotent posting, and GL integration before broad scaffolding work.
4. **P1 — inventory lifecycle:** prove stock movement invariants, non-negative-stock policy, warehouse/company isolation, and ledger/costing impact with DB-backed tests.
5. **P2 — scaffold hygiene:** once canonical implementations are identified, remove unused empty placeholders or replace them with explicit, documented adapters. Do not bulk-fill files with stubs just to change the byte count.

## Verification boundary
- This audit used the tracked Git tree only.
- It did not execute business workflows against PostgreSQL and does not establish runtime API coverage.
- The Windows self-hosted release gate passed on the current pre-audit commit `16a7a20a866fe27c1a0649b1e298fe73ca5005f2` (run [40738561764](https://github.com/ahmedgamalelnoby-prog/PrimeERP/actions/runs/40738561764)). The new audit document itself will need a fresh run after commit.
- The existing module catalog's conservative “in progress” labels are appropriate; do not mark these workflows complete based only on registry presence or route fallbacks.
