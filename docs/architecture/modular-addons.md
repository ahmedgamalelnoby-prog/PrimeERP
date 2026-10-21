# PrimeERP Modular Add-on Architecture

PrimeERP uses a modular-monolith architecture with Odoo-inspired add-on boundaries, adapted for FastAPI, React and multi-tenant SaaS.

## Rules

1. A business capability is an add-on; a button or trivial helper is not.
2. Every add-on owns its backend API, schemas, services, security, migrations and tests where applicable.
3. Every add-on exposes a `__manifest__.py` containing stable metadata and declared dependencies.
4. Dependencies use technical names such as `accounting/accounting_core` and must form an acyclic graph.
5. Optional integrations must communicate through contracts/events rather than hard imports into unrelated domains.
6. Existing legacy modules are migrated incrementally. Compatibility adapters preserve existing routes while ownership moves to add-ons.
7. Tenant entitlements and user permissions are separate concerns: installation does not automatically grant access.
8. Financial records are never removed as part of module disable/uninstall; retention and reversal policies remain authoritative.

## Target layout

```text
backend/app/modules/<domain>/<addon>/
    __manifest__.py
    __init__.py
    models/
    schemas/
    services/
    api/
    security/
    data/
    migrations/
    tests/
```

The frontend follows the same ownership model under `frontend/src/modules/<domain>/<addon>/`.

## Migration strategy

New capabilities must use the add-on contract first. Existing large modules are migrated in slices rather than mechanically moving every file. During migration, adapters keep public APIs stable. A domain is considered migrated only after its old ownership is removed and CI verifies the new dependency graph.

## Current foundation

The module engine currently provides manifest metadata, filesystem discovery, dependency validation, lifecycle state and a process-wide registry. Accounting, Sales and Inventory now have initial add-on boundaries that can be expanded without breaking the legacy implementation.
