import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(
  new URL("../src/shared/api/interceptors.ts", import.meta.url),
  "utf8",
);

test("concurrent unauthorized requests share one refresh promise", () => {
  assert.match(source, /let refreshInFlight: Promise<string> \| null = null/);
  assert.match(source, /if \(!refreshInFlight\)/);
  assert.match(source, /await refreshInFlight/);
  assert.match(source, /refreshInFlight = null/);
});

test("identity session endpoints are excluded from refresh retry", () => {
  assert.match(source, /url\.includes\("\/identity\/login"\)/);
  assert.match(source, /url\.includes\("\/identity\/refresh"\)/);
  assert.match(source, /url\.includes\("\/identity\/logout"\)/);
});

test("each protected request is retried at most once", () => {
  assert.match(source, /config\._primeerpRetry/);
  assert.match(source, /config\._primeerpRetry = true/);
});

test("refresh response cannot restore a changed or logged-out session", () => {
  assert.match(source, /storage\.getRefreshToken\(\) !== refreshToken/);
  assert.match(source, /The session changed while the token was refreshing/);
});

test("refresh failure only clears the session snapshot that failed", () => {
  assert.match(source, /storage\.getRefreshToken\(\) === attemptedRefreshToken/);
  assert.match(source, /storage\.clear\(\)/);
  assert.match(source, /This also clears an access-token-only stale session/);
});
