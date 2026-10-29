import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const readRepoFile = (path) => readFileSync(resolve(here, "../../", path), "utf8");

const catalogPage = readRepoFile("frontend/src/modules/platform/pages/ModuleCatalogPage.tsx");
const router = readRepoFile("frontend/src/app/router/AppRouter.tsx");
const entitlementGuard = readRepoFile("frontend/src/app/router/EntitlementGuard.tsx");
const moduleWorkbench = readRepoFile("frontend/src/modules/platform/pages/ModuleWorkbenchPage.tsx");
const moduleRegistry = readRepoFile("backend/app/modules/platform/module_registry.py");
const settingsRegistry = readRepoFile("backend/app/modules/company_settings/registry.py");
const authSchema = readRepoFile("backend/app/modules/identity/schemas/auth.py");
const authRouter = readRepoFile("backend/app/modules/identity/api/router.py");
const authService = readRepoFile("backend/app/modules/identity/services/authentication_service.py");
const navigation = readRepoFile("frontend/src/app/navigation.ts");
const sidebar = readRepoFile("frontend/src/components/layout/AppSidebar.tsx");

function registryKeys(source) {
  return [...source.matchAll(/\{"key": "([^"]+)"/g)].map((match) => match[1]);
}

function targetEntries(source) {
  return [...source.matchAll(/^\s*("?[-\w]+"?): \{ path: "([^"]+)", operational: (true|false) \},?$/gm)]
    .map((match) => ({ key: match[1].replace(/^"|"$/g, ""), path: match[2], operational: match[3] === "true" }));
}

test("every backend module registry key has a catalog navigation target", () => {
  const keys = registryKeys(moduleRegistry);
  const targets = targetEntries(catalogPage);
  const targetKeys = new Set(targets.map((target) => target.key));
  const missing = keys.filter((key) => !targetKeys.has(key));

  assert.equal(keys.length, 57, "update this contract when the backend module registry intentionally changes");
  assert.deepEqual(missing, []);
  assert.equal(new Set(keys).size, keys.length, "backend module keys must be unique");
});

test("every catalog target resolves to a declared route or the module workbench", () => {
  const targets = targetEntries(catalogPage);
  const routes = new Set([...router.matchAll(/<Route path="([^"]+)"/g)].map((match) => match[1]));
  const unresolved = targets
    .filter(({ path }) => !routes.has(path) && !path.startsWith("/modules/"))
    .map(({ key, path }) => ({ key, path }));

  assert.ok(catalogPage.includes('onClick={()=>navigate(moduleTargets[i.key]?.path||("/modules/"+encodeURIComponent(i.key)))}'),
    "each catalog entry should expose a working navigation action");
  assert.ok(catalogPage.includes("واجهة مخصصة") && catalogPage.includes("قيد الاستكمال"),
    "catalog should distinguish dedicated screens from work-in-progress screens");
  assert.deepEqual(unresolved, []);
});

test("company settings registry counts and integration status remain explicit", () => {
  const entries = settingsRegistry.split("\n").filter((line) => /^\s*\("[^"]+"/.test(line));
  const runtime = entries.filter((line) => /"runtime"\),?$/.test(line));
  const catalog = entries.filter((line) => /"catalog"\),?$/.test(line));
  const keys = entries.map((line) => line.match(/^\s*\("([^"]+)"/)?.[1]).filter(Boolean);
  const catalogKeys = catalog.map((line) => line.match(/^\s*\("([^"]+)"/)?.[1]);

  assert.equal(entries.length, 75, "update this contract when settings are intentionally added or removed");
  assert.equal(runtime.length, 72);
  assert.deepEqual(catalogKeys, [
    "hr.attendance_source",
    "hr.biometric_sync_interval_minutes",
    "pos.allow_open_cash_drawer",
  ]);
  assert.equal(new Set(keys).size, keys.length, "company setting keys must be unique");
});

test("tenant module workbench routes enforce module entitlements without blocking enabled tenants", () => {
  assert.ok(entitlementGuard.includes('pathname === path || (path !== "/modules" && matchesPath(pathname, path))'),
    "the module catalog must be platform-only without treating every workbench path as the catalog");
  assert.ok(entitlementGuard.includes('if (pathname.startsWith("/modules/"))'),
    "generic module routes need their own entitlement decision");
  assert.ok(entitlementGuard.includes('WORKBENCH_ALIASES[decodedKey] || decodedKey.replace(/-/g, "_")'),
    "hyphenated module aliases must resolve to the backend entitlement key");
  assert.ok(entitlementGuard.includes('user.enabled_modules?.includes(moduleCode) || user.enabled_modules?.includes(decodedKey)'),
    "a tenant with the matching module entitlement must be able to open its workbench");
  assert.ok(entitlementGuard.includes('if (isPlatformAdmin) return <Outlet />'),
    "platform administrators retain access to module workbench routes");
});


test("module workbench normalizes catalog aliases before registry lookup", () => {
  assert.ok(moduleWorkbench.includes('"egyptian-einvoice":"einvoice"'),
    "Egyptian e-invoice catalog aliases must resolve to the canonical registry key");
  assert.ok(moduleWorkbench.includes('moduleKey.replace(/-/g,"_")'),
    "hyphenated module keys must normalize to registry underscore keys");
  assert.ok(moduleWorkbench.includes('encodeURIComponent(registryKey)'),
    "the registry API lookup must use the normalized key");
  assert.ok(moduleWorkbench.includes('},[registryKey]);'),
    "the effect must refresh when the normalized registry key changes");
});


test("navigation filters permission-tagged entries using authenticated role grants", () => {
  assert.ok(authSchema.includes("permissions: list[str] = Field(default_factory=list)"));
  assert.ok(authRouter.includes('"permissions": permissions'));
  assert.ok(authService.includes('"permissions": permission_names'));
  assert.ok(navigation.includes("if (item.permission && !grantedNames.has(item.permission.toLowerCase())) return false"));
  assert.ok(navigation.includes("permissionNames: string[] = []"));
  assert.ok(sidebar.includes("user?.permissions ?? []"));
  assert.ok(sidebar.includes("user?.permissions, user?.is_platform_admin"));
});


test("protected route metadata includes role grants before rendering pages", () => {
  assert.ok(entitlementGuard.includes("PERMISSION_PATHS"));
  assert.ok(entitlementGuard.includes("requiredPermission"));
  assert.ok(entitlementGuard.includes("user.permissions"));
  assert.ok(entitlementGuard.indexOf("permissionRule") < entitlementGuard.indexOf("if (CORE_PATHS.some"));
});


test("direct navigation to a permission-tagged screen checks the same role grant as the sidebar", () => {
  assert.ok(navigation.includes("export function getRequiredNavigationPermission(pathname: string)"));
  assert.ok(navigation.includes('normalizedPath.startsWith(itemPath + "/")'),
    "nested paths should inherit the most specific navigation permission");
  assert.ok(entitlementGuard.includes("getRequiredNavigationPermission(pathname)"),
    "the route guard must enforce navigation permission metadata on direct URL entry");
  assert.ok(entitlementGuard.includes("permission.trim().toLowerCase() === navigationPermission.toLowerCase()"),
    "a user without the route grant must not render a permission-tagged page");
});
