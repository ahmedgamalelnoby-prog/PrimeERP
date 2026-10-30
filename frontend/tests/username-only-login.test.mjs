import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const loginPage = await readFile(
  new URL("../src/modules/identity/pages/LoginPage.tsx", import.meta.url),
  "utf8",
);
const loginForm = await readFile(
  new URL("../src/modules/identity/components/LoginForm.tsx", import.meta.url),
  "utf8",
);
const authService = await readFile(
  new URL("../src/modules/identity/services/authentication.service.ts", import.meta.url),
  "utf8",
);
const authContext = await readFile(
  new URL("../src/modules/identity/context/AuthContext.tsx", import.meta.url),
  "utf8",
);
const storage = await readFile(
  new URL("../src/shared/utils/storage.ts", import.meta.url),
  "utf8",
);

test("primary sign-in screen asks only for username and password", () => {
  assert.match(loginPage, /id="login"/);
  assert.match(loginPage, /id="password"/);
  assert.doesNotMatch(loginPage, /companyName|tenantSlug|tenant_name|tenant_slug/);
  assert.match(loginPage, /await login\(normalizedLogin, password\)/);
});

test("shared login form does not request a tenant identifier", () => {
  assert.doesNotMatch(loginForm, /tenantSlug|tenant_slug|tenant_name|كود المؤسسة/);
});

test("standard login payload contains only credentials unless an explicit legacy tenant filter is supplied", () => {
  assert.match(authService, /login: loginValue/);
  assert.match(authService, /password: payload\.password/);
  assert.match(authService, /payload\.tenant_slug\?\.trim\(\)/);
  assert.match(authService, /payload\.tenant_name\?\.trim\(\)/);
});

test("restored sessions synchronize tenant context from the authenticated user", () => {
  assert.match(authContext, /storage\.setTenantId\(currentUser\.tenant_id\)/);
});

test("logout clears the remembered company selection", () => {
  assert.match(storage, /localStorage\.removeItem\("company_id"\)/);
});
