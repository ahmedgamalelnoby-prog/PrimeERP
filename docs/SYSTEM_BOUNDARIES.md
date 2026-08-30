# System Boundaries

PrimeERP is an independent product repository focused on restaurant ERP operations.

## Backend
- Owns PrimeERP business domains, APIs, database models and migrations.
- Must not import application source code from CommercialERP or ContentAI.

## Frontend
- Owns PrimeERP routes, screens, API clients and UI components.
- Must call only PrimeERP backend APIs.

## Isolation rules
- No cross-repository source imports.
- No shared runtime database between products.
- Environment variables remain product-specific.
- Dependencies remain product-specific.
- PrimeERP CI validates backend, frontend and repository hygiene independently.

Shared engineering conventions are allowed, but shared application code should be introduced only as an explicit versioned package.
