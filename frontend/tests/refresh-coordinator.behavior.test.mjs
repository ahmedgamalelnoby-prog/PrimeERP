import assert from "node:assert/strict";
import test from "node:test";
import {
  createRefreshCoordinator,
  shouldClearFailedSession,
} from "../src/shared/api/refreshCoordinator.mjs";

test("concurrent callers share one refresh promise and token snapshot", async () => {
  const coordinator = createRefreshCoordinator();
  let refreshCalls = 0;
  let refreshTokenPassed;
  let resolveRefresh;
  const refresh = (token) => {
    refreshCalls += 1;
    refreshTokenPassed = token;
    return new Promise((resolve) => { resolveRefresh = resolve; });
  };
  const getToken = () => "refresh-old";

  const first = coordinator.run(getToken, refresh);
  const second = coordinator.run(getToken, refresh);
  assert.equal(first.promise, second.promise);
  assert.equal(first.refreshTokenUsed, "refresh-old");
  assert.equal(second.refreshTokenUsed, "refresh-old");
  await Promise.resolve();
  assert.equal(refreshCalls, 1);
  assert.equal(refreshTokenPassed, "refresh-old");

  resolveRefresh("access-new");
  assert.equal(await first.promise, "access-new");
  assert.equal(await second.promise, "access-new");
});

test("refresh receives the token snapshot captured before its async start", async () => {
  const coordinator = createRefreshCoordinator();
  let currentToken = "refresh-before-login";
  let tokenSent;
  const attempt = coordinator.run(
    () => currentToken,
    async (snapshot) => {
      tokenSent = snapshot;
      return "access";
    },
  );

  // Simulate a new login before the queued refresh callback begins.
  currentToken = "refresh-new-login";
  assert.equal(await attempt.promise, "access");
  assert.equal(tokenSent, "refresh-before-login");
  assert.equal(attempt.refreshTokenUsed, "refresh-before-login");
});

test("a settled refresh releases the coordinator for a later session", async () => {
  const coordinator = createRefreshCoordinator();
  const first = coordinator.run(() => "refresh-1", async () => "access-1");
  assert.equal(await first.promise, "access-1");

  const second = coordinator.run(() => "refresh-2", async () => "access-2");
  assert.notEqual(first.promise, second.promise);
  assert.equal(second.refreshTokenUsed, "refresh-2");
  assert.equal(await second.promise, "access-2");
});

test("failed refresh clears only the session snapshot that failed", () => {
  assert.equal(shouldClearFailedSession("refresh-old", "refresh-old"), true);
  assert.equal(shouldClearFailedSession("refresh-new", "refresh-old"), false);
  assert.equal(shouldClearFailedSession(null, "refresh-old"), false);
  assert.equal(shouldClearFailedSession(null, null), true);
});
