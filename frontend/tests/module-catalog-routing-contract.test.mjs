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
const moduleRegistry = readRepoFile("backend/app/modules/platform/module_registry.py");
const settingsRegistry = readRepoFile("backend/app/modules/company_settings/registry.py");

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
