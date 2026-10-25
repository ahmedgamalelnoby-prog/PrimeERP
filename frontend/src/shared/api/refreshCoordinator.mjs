export function createRefreshCoordinator() {
  let inFlight = null;
  let tokenUsed = null;
  return {
    run(getRefreshToken, refresh) {
      if (!inFlight) {
        tokenUsed = getRefreshToken();
        inFlight = Promise.resolve().then(refresh).finally(() => {
          inFlight = null;
          tokenUsed = null;
        });
      }
      return { promise: inFlight, refreshTokenUsed: tokenUsed };
    },
  };
}

export function shouldClearFailedSession(currentRefreshToken, attemptedRefreshToken) {
  return currentRefreshToken === attemptedRefreshToken;
}
