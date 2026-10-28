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
- Added a backend contract test asserting both module-registry GET routes declare the `get_current_user` authentication dependency. This verifies route wiring at source level, not HTTP 401 behavior or role-specific authorization.
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
- CI was queued for commit `fad7d83efbf99e684bfbe7f4ac1012696fac46a1` after this test was added. Do not treat the new test as passed until that workflow finishes.
- This test does not yet exercise an unauthenticated HTTP request, a tenant session, or a platform-admin session. Those require live/request-level coverage.
