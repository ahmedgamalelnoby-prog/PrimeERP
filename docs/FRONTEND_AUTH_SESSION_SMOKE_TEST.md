# Frontend Authentication Session Smoke Tests

## Scope

Use this checklist against a disposable development/test tenant. Do not use production credentials or a production browser session. The release gate verifies compile/build and service health, but does not simulate browser storage races or real interactive login.

## Preconditions

- Backend and frontend are running from the same PR branch.
- A valid test user and tenant are available.
- Browser DevTools Network and Application/Storage panels are open.
- Record the frontend build/commit SHA used for the run.

## Scenarios

### 1. Normal login and current-user bootstrap

1. Clear site storage.
2. Log in with a valid test account and tenant.
3. Confirm login succeeds and the expected user/company context is displayed.
4. Inspect local storage: access token and refresh token should both exist; tenant ID should be set when the selected tenant requires it.
5. Reload the page and confirm the session bootstraps through the current-user endpoint without a second login.

Expected: no password or token values are printed to the console or application logs.

### 2. Expired access token with valid refresh token

1. Keep the session logged in.
2. In a disposable test environment, make the access token invalid/expired while preserving the valid refresh token.
3. Trigger two or more authenticated API requests close together.
4. Inspect Network requests.

Expected: requests share a single in-flight refresh operation; successful refresh stores the returned token pair and retries each original request at most once.

### 3. Expired/invalid refresh token

1. In a disposable test environment, replace the refresh token with an invalid value.
2. Trigger an authenticated request that returns 401.

Expected: refresh fails without an interceptor loop; the failed session's local auth state is cleared and the application returns to its unauthenticated flow.

### 4. Access token exists but refresh token is missing

1. In local storage, remove only the refresh token while leaving the access token.
2. Trigger an authenticated request that returns 401.

Expected: the stale session is cleared; repeated requests do not remain stuck using an access-token-only session.

### 5. Logout while refresh is pending

1. Use DevTools throttling or a test proxy to delay the refresh response.
2. Trigger an authenticated request that initiates refresh.
3. Log out before the refresh response returns.
4. Allow the delayed response to complete.

Expected: the late refresh response does not recreate the logged-out session; access token, refresh token, and tenant ID remain cleared.

### 6. New login while an old refresh is pending

1. Delay a refresh request for session A.
2. Log out and log in as a different test user/session B before the old response completes.
3. Allow the old response to complete.

Expected: session A's response cannot overwrite session B's token pair, and failure cleanup for session A cannot clear session B.

### 7. Logout with network unavailable

1. Log in with a test account.
2. Simulate network loss and log out.

Expected: local session state clears immediately even if server-side revocation cannot be confirmed. The server-side refresh token should expire/revoke according to backend policy.

## Evidence to record

For each scenario record Pass/Fail, commit SHA, browser, console errors, and relevant request status codes. Never attach raw access/refresh tokens, passwords, or full Authorization headers.

## Automation status

The frontend now has a Node built-in `node:test` suite at `frontend/tests/auth-session-contract.test.mjs`, run by `npm test` and included in the self-hosted Release Gate. These automated checks validate source-code contracts for refresh coalescing, identity endpoint exclusions, one-retry protection, stale-response protection, and session-scoped cleanup. They are static contract checks—not behavioral Axios simulations or browser E2E tests.

The seven scenarios above remain manual regression scenarios. Do not mark them passed until executed against a running app with a disposable test account. The latest confirmed self-hosted Release Gate run is [Run #4111](https://github.com/ahmedgamalelnoby-prog/PrimeERP/actions/runs/40234708686), which completed successfully with `npm test`, typecheck, lint, and build.
