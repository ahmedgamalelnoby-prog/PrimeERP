import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(
  new URL("../src/shared/api/interceptors.ts", import.meta.url),
  "utf8",
);

test("interceptor delegates refresh coordination to the tested coordinator", () => {
  assert.match(source, /createRefreshCoordinator/);
  assert.match(source, /refreshCoordinator\.run/);
  assert.match(source, /await refreshAttempt\.promise/);
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

test("refresh failure only clears the attempted session snapshot", () => {
  assert.match(source, /shouldClearFailedSession\(storage\.getRefreshToken\(\), attemptedRefreshToken\)/);
  assert.match(source, /storage\.clear\(\)/);
});
