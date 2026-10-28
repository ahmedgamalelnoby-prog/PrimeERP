# PrimeERP module visibility and company-settings audit — 2026-10-28

## Scope
Reviewed GitHub branch `feature/primeerp-modern-ui-i18n-theme-settings-20261027` and added a visibility/navigation improvement on branch `feature/primeerp-completion-visibility-20261028`. This is a source-code and CI audit; browser tests against a live backend and role-specific session tests have not been executed from this environment.

## Module registry and navigation
- Backend module registry contains **57 module keys**.
- The catalog now provides an explicit route target for each backend module key, with aliases for older UI keys (for example `cost_centers` / `cost-centers`, `einvoice` / `egyptian-einvoice`, and `time_tracking` / `time-tracking`).
- Every catalog card now has an accessible **Open module** action.
- Each card distinguishes a dedicated screen from a screen/workbench that remains in progress. The label is intentionally conservative; it does not claim that every backend workflow is complete.
- Navigation now exposes direct entries for CRM, HR, POS, Manufacturing, Commerce, and Mobile, filtered using the existing enabled-module logic.
- Module catalog screen targets without a dedicated screen fall back to the registry workbench at `/modules/:moduleKey`.
- Backend module status and UI screen readiness are separate signals. A registry status of `active` is not proof that every related workflow is complete.

### Follow-up required
- Frontend entitlement guard now treats `/modules` (the catalog) as platform-only while checking `/modules/:moduleKey` against the tenant's enabled modules. It normalizes common hyphen/underscore aliases and fails closed for unknown workbench keys.
- Added backend checks that both module-registry GET routes declare the `get_current_user` dependency and that unauthenticated requests to the list/detail endpoints return HTTP 401 through FastAPI TestClient.
- Continue authorization auditing at the API level, and add live platform-admin/tenant session tests. The navigation helper filters by enabled modules but does not itself evaluate each item's `permission` field; frontend checks are not a substitute for backend authorization.
- Several routes still use generic pages or the registry workbench. These are explicitly marked as in progress from the catalog, and need domain-specific screens and workflow tests before being described as complete.
- Browser smoke tests must cover platform-admin and tenant users, direct URL entry, refresh on nested routes, and denied module entitlements.

## Company settings registry
The live source registry currently defines **75 settings**, not 68:
- **72** are marked `runtime`.
- **3** remain `catalog`, meaning visible/persistable but not proven to be consumed by a complete owning workflow.

The remaining catalog settings are:
- `hr.attendance_source`
- `hr.biometric_sync_interval_minutes`
- `pos.allow_open_cash_drawer`

The release-gate backend tests explicitly require these three policies to remain catalog-only until a verified end-to-end consumer exists. A route guard or authorization endpoint alone does not prove that the selected attendance source changes the attendance workflow or that a physical cash drawer is opened through a configured terminal driver. Keep these statuses conservative until integration tests prove the full behavior.

## Dependency/security commit
The local commit `3a5e17b2` was not present on the GitHub feature branch at the time of this audit. Its Vite/React Router dependency changes must be pushed from the user's local checkout, then verified on GitHub and tested in CI before merge.

## Verification status
- Static source review: completed for the module registry, catalog, navigation, routes, and company-settings registry.
- Frontend build/test/audit: previously passed on the user's local checkout after the dependency upgrade, but those results do not apply to this branch's older dependency manifest.
- Authenticated-user responses now expose active permission names assigned through the user's active role; the navigation uses these names to filter permission-tagged entries.
- The route guard now checks required permissions for core and module URLs before rendering protected screens. This is UI defense-in-depth only; backend API dependencies remain the security boundary.
- Release-gate run `40719154712` failed at Docker Compose network creation, not application tests: Docker reported `all predefined address pools have been fully subnetted`. A workflow preflight now removes only empty stale networks named `primeerp-ci-*`; a fresh CI run must verify this fix.
- Live browser/API authorization tests: not run.
- Merge: not performed; keep changes in a reviewable pull request until CI and smoke tests pass.

## Follow-up implementation — tenant workbench entitlement fix
- Fixed a route-guard conflict where the broad `/modules` platform-only rule also blocked every `/modules/:moduleKey` workbench from tenant users, even when the tenant had that module enabled.
- Kept the catalog itself platform-only; workbench routes now resolve their module entitlement, support hyphen/underscore aliases, allow platform admins, and deny unknown/unentitled keys.
- Added a source-contract test for the guard behavior. This is a static contract test; it is not a substitute for real authenticated browser/API smoke tests.
- Normalized module workbench aliases before registry lookup (including `egyptian-einvoice` → `einvoice`) and added a contract test for the normalization.


## CI failure analysis and correction
- The Windows release gate ran **761 passed, 2 failed, 2 skipped** backend tests. Both failures were in `tests/test_company_settings_registry.py` because attendance source and standalone cash-drawer opening were marked runtime despite the explicit catalog-only contract.
- Reverted those two statuses to `catalog` and updated the frontend registry-count contract to **72 runtime / 3 catalog**. This preserves the existing backend policy contract instead of weakening tests to match an unverified status.
- The Windows self-hosted release gate passed on commit `2e6c59e4`, including backend unit tests, Salla/shipping contracts, Alembic graph/import smoke, frontend install/build, Compose validation, production image builds, PostgreSQL effective-date guard tests, service startup, and runtime health checks.
- After workbench alias normalization and its contract test were added, the release gate passed again on commit `dd3f53bf` (workflow run `40674285261`). The separate browser/API authorization smoke tests remain outstanding.


## Latest authorization contract check — 2026-10-28
- Added `test_module_registry_api_requires_authenticated_user_dependency` to ensure `/platform/modules` and `/platform/modules/{module_key}` both retain the authenticated-user dependency in FastAPI route metadata.
- Added a request-level TestClient regression test requiring HTTP 401 from the list and detail endpoints when no access token is supplied.
- Windows self-hosted release gate passed on commit `405912bcd506284738c2808fac68ac0d9289cc70` (workflow run `40712260595`), including the new request-level authentication test.
- The new TestClient check covers unauthenticated requests. Tenant and platform-admin session behavior, entitlement denial at the UI/API boundary, direct URL entry, and nested-route refresh still require role-specific/browser smoke coverage.
- Code review confirmed the current `AuthenticatedUser` frontend contract contains `enabled_modules` but no permission list, and navigation entries' `permission` strings are not evaluated by `getVisibleNavigationItems`. Do not treat hidden navigation as security enforcement; backend endpoints must enforce permissions. Adding UI permission filtering requires a trustworthy permission payload or a dedicated permissions endpoint and should be tested against actual role assignments.

## Targeted functional-gap pass — 2026-10-28

This pass is a source-code review, not a live end-to-end certification.

### Confirmed UI/workflow gaps
- The generic `ModuleWorkbenchPage` is a module-registry information page (description, group, status, AI-help link); it does not itself implement the module's domain transactions. Catalog targets using this fallback must remain explicitly marked as in progress.
- The report center deliberately disables several report entries because their concrete report pages are not present yet: general ledger/trial balance, treasury, sales, purchasing, profitability, inventory, stock counts, HR attendance/payroll, hospitality, leasing, and audit log. These must not be represented as operational reports until implemented and tested.
- The router contains a generic fallback page for unknown routes. A successful SPA route render is not evidence of a working business workflow.
- CRM, HR, POS, manufacturing, and common commerce screens do call backend APIs, but this source review did not execute their full create/edit/approve/post/report lifecycles against a live database. These workflows remain unverified rather than certified complete.

### Authorization correction
- Added a route-permission resolver that derives the required grant from the same navigation metadata used by the sidebar.
- The route guard now checks that grant on direct URL entry as well as the existing tenant-module entitlement checks. Nested routes use the most specific matching navigation path.
- Permission-name comparison is case-insensitive and trims whitespace.
- Added a frontend contract test for direct route permission enforcement. This is a frontend UX/defense-in-depth check only; backend endpoint authorization remains authoritative.

### CI reliability correction
- The latest failing release-gate run had passed backend tests, frontend build, Compose validation, and production image builds. It failed before migrations because Docker reported `all predefined address pools have been fully subnetted`; the migration container was never created. This was an infrastructure/network allocation failure, not a migration assertion failure.
- The workflow now removes only stale containers named with the dedicated `primeerp-ci-*` prefix before reclaiming empty stale networks with that same prefix. It does not prune unrelated Docker networks or containers.
- The latest changes require a fresh release-gate run before the CI result can be considered verified.

### Remaining verification required
1. Run role-based browser checks for platform admin, tenant admin, and restricted tenant roles: sidebar visibility, direct URL entry, refresh, and API denial.
2. Execute CRUD and lifecycle tests for sales/purchases, accounting posting, inventory movements, payroll approvals, attendance corrections, POS cash drawer/shift, and integration retries.
3. Verify each company setting changes its owning workflow end-to-end; keep the three catalog-only settings listed above unverified until then.
4. Replace generic workbench routes with domain-specific screens only after each workflow has a documented API contract and regression tests.
