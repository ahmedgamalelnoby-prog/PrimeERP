export interface RefreshCoordinator {
  run<T>(
    getRefreshToken: () => string | null,
    refresh: (refreshToken: string | null) => Promise<T>,
  ): {
    promise: Promise<T>;
    refreshTokenUsed: string | null;
  };
}
export function createRefreshCoordinator(): RefreshCoordinator;
export function shouldClearFailedSession(currentRefreshToken: string | null, attemptedRefreshToken: string | null): boolean;
