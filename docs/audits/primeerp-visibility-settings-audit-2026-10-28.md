# PrimeERP module visibility and company-settings audit — 2026-10-28

## Scope
Reviewed GitHub branch `feature/primeerp-modern-ui-i18n-theme-settings-20261027` and added a visibility/navigation improvement on branch `feature/primeerp-completion-visibility-20261028`. This is a source-code audit; browser tests against a live backend and role-specific session tests have not been executed from this environment.

## Module registry and navigation
- Backend module registry contains **57 module keys**.
- The catalog now provides an explicit route target for each backend module key, with aliases for older UI keys (for example `cost_centers` / `cost-centers`, `einvoice` / `egyptian-einvoice`, and `time_tracking` / `time-tracking`).
- Every catalog card now has an accessible **Open module** action.
- Each card distinguishes a dedicated screen from a screen/workbench that remains in progress. The label is intentionally conservative; it does not claim that every backend workflow is complete.
- Navigation now exposes direct entries for CRM, HR, POS, Manufacturing, Commerce, and Mobile, filtered using the existing enabled-module logic.
- Module catalog screen targets without a dedicated screen fall back to the registry workbench at `/modules/:moduleKey`.
- Backend module status and UI screen readiness are separate signals. A registry status of `active` is not proof that every related workflow is complete.

### Follow-up required
- Audit authorization at the route/API level, not only menu visibility. The current navigation helper filters by enabled modules; it does not itself evaluate each item's `permission` field.
- Several routes still use generic pages or the registry workbench. These are explicitly marked as in progress from the catalog, and need domain-specific screens and workflow tests before being described as complete.
- Browser smoke tests must cover platform-admin and tenant users, direct URL entry, refresh on nested routes, and denied module entitlements.

## Company settings registry
The live source registry currently defines **75 settings**, not 68:
- **74** are marked `runtime`.
- **1** remains `catalog`, meaning persisted/visible but not yet consumed by the owning workflow.

The remaining catalog setting is:
- `hr.biometric_sync_interval_minutes`

The attendance-source and cash-drawer policies were promoted to `runtime` because the HR attendance guard and POS cash-drawer authorization endpoint already consume them. Do not promote the remaining biometric polling interval until a real scheduled/connector workflow consumes it and tests prove the interval controls polling.

## Dependency/security commit
The local commit `3a5e17b2` was not present on the GitHub feature branch at the time of this audit. Its Vite/React Router dependency changes must be pushed from the user's local checkout, then verified on GitHub and tested in CI before merge.

## Verification status
- Static source review: completed for the module registry, catalog, navigation, routes, and company-settings registry.
- Frontend build/test/audit: previously passed on the user's local checkout after the dependency upgrade, but those results do not apply to this branch's older dependency manifest.
- Live browser/API authorization tests: not run.
- Merge: not performed; keep changes in a reviewable pull request until CI and smoke tests pass.
