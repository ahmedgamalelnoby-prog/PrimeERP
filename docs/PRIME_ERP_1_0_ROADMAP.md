# PrimeERP 1.0 Execution Roadmap

## Wave A — Financial & Transaction Core
- Universal state machine
- Posting engine
- AR/AP lifecycle
- Reconciliation
- Period close/lock
- Audit/security hardening

Exit gate: operational documents can create, post, reverse and reconcile accounting entries without direct mutation of posted records.

## Wave B — Commerce & Inventory
- Product/SKU/UOM master
- Pricing/tax
- Sales lifecycle
- Purchasing lifecycle
- Warehouse/WMS
- FIFO/weighted-average/standard costing
- Returns

Exit gate: order-to-cash and procure-to-pay are fully traceable to inventory and GL.

## Wave C — Operations
- Manufacturing/MRP
- Recipe/BOM
- POS
- Restaurant
- Shipping
- Carrier settlement

Exit gate: operational consumption, revenue, cost, stock and settlement reconcile.

## Wave D — Connectivity
- Integration Hub
- Salla
- Webhooks/retries/idempotency
- External mapping
- Reconciliation dashboards

Exit gate: external order/channel data can be replayed safely and reconciled.

## Wave E — Enterprise
- CRM
- HR/Payroll
- Projects
- Contracts
- Approvals/workflows
- Enterprise finance

Exit gate: departments can run their operational cycles without bypassing core controls.

## Wave F — Intelligence & Platform
- BI
- AI analysis
- AI anomaly detection
- AI forecasting
- AI action with approval
- Mobile
- Developer APIs/extensions
- Localization adapters

Exit gate: PrimeERP is a coherent SaaS ERP platform rather than a collection of modules.

## Working rule
Every wave must leave the repository in a releasable state. New functionality must include tests and must not weaken existing lifecycle, accounting, tenant isolation or idempotency guarantees.
