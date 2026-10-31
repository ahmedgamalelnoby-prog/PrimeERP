import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";
import assert from "node:assert/strict";

const source = (path) =>
  readFileSync(join(process.cwd(), path), "utf8");

test("users table exposes company assignment action", () => {
  const table = source("src/modules/users/components/UserTable.tsx");
  const page = source("src/modules/users/pages/UsersPage.tsx");
  assert.match(table, /onManageCompanies/);
  assert.match(table, /Building2/);
  assert.match(page, /UserCompanyAccessDialog/);
});

test("company assignment dialog loads allowed and available companies", () => {
  const dialog = source("src/modules/users/components/UserCompanyAccessDialog.tsx");
  assert.match(dialog, /getAvailableCompanies/);
  assert.match(dialog, /getCompanyAccess/);
  assert.match(dialog, /default_company_id/);
  assert.match(dialog, /updateCompanyAccess/);
});

test("users API exposes company assignment endpoints", () => {
  const api = source("src/modules/users/api/users.api.ts");
  assert.match(api, /companies\/available/);
  assert.match(api, /companies`/);
  assert.match(api, /company_ids/);
});

test("company-independent bootstrap and user administration omit stale company header", () => {
  const client = source("src/shared/api/client.ts");
  assert.match(client, /requestPath === "\/companies"/);
  assert.match(client, /requestPath.startsWith\("\/identity\/users"\)/);
  assert.match(client, /X-Company-ID/);
});
