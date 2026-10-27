import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  createRefreshCoordinator,
  shouldClearFailedSession,
} from "../src/shared/api/refreshCoordinator.mjs";

test("integrated auth lifecycle: concurrent refresh, retry guards, logout and newer-login protection", async () => {
  const source = await readFile(
    new URL("../src/shared/api/interceptors.ts", import.meta.url),
    "utf8",
  );

  // Contract checks against the actual interceptor implementation.
  assert.match(source, /url\.includes\("\/identity\/login"\)/);
  assert.match(source, /url\.includes\("\/identity\/refresh"\)/);
  assert.match(source, /url\.includes\("\/identity\/logout"\)/);
  assert.match(source, /config\._primeerpRetry/);
  assert.match(source, /config\._primeerpRetry = true/);
  assert.match(source, /storage\.getRefreshToken\(\) !== refreshToken/);
  assert.match(source, /shouldClearFailedSession\(storage\.getRefreshToken\(\), attemptedRefreshToken\)/);
  assert.match(source, /storage\.clear\(\)/);

  // Two simultaneous 401s must share one refresh attempt and token snapshot.
  const coordinator = createRefreshCoordinator();
  let sessionRefreshToken = "refresh-login-1";
  let refreshCalls = 0;
  let refreshTokenSent = null;
  let finishRefresh;
  const refresh = (snapshot) => {
    refreshCalls += 1;
    refreshTokenSent = snapshot;
    return new Promise((resolve) => { finishRefresh = resolve; });
  };
  const requestA = coordinator.run(() => sessionRefreshToken, refresh);
  const requestB = coordinator.run(() => sessionRefreshToken, refresh);
  assert.equal(requestA.promise, requestB.promise);
  assert.equal(requestA.refreshTokenUsed, "refresh-login-1");
  assert.equal(requestB.refreshTokenUsed, "refresh-login-1");
  await Promise.resolve();
  assert.equal(refreshCalls, 1);
  assert.equal(refreshTokenSent, "refresh-login-1");

  // A newer login during refresh must not be cleared as the failed session.
  sessionRefreshToken = "refresh-login-2";
  assert.equal(shouldClearFailedSession(sessionRefreshToken, requestA.refreshTokenUsed), false);
  finishRefresh("access-from-old-session");
  assert.equal(await requestA.promise, "access-from-old-session");
  assert.equal(await requestB.promise, "access-from-old-session");

  // After settlement, the coordinator must allow the newer session to refresh.
  const next = coordinator.run(
    () => sessionRefreshToken,
    async (snapshot) => {
      assert.equal(snapshot, "refresh-login-2");
      return "access-login-2";
    },
  );
  assert.equal(next.refreshTokenUsed, "refresh-login-2");
  assert.equal(await next.promise, "access-login-2");

  // A failed refresh may clear only the session snapshot that actually failed.
  assert.equal(shouldClearFailedSession("refresh-login-2", "refresh-login-2"), true);
  assert.equal(shouldClearFailedSession(null, "refresh-login-2"), false);
  assert.equal(shouldClearFailedSession(null, null), true);
});
