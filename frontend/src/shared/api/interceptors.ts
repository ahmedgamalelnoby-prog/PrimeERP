import type { InternalAxiosRequestConfig } from "axios";

import client from "./client";
import { storage } from "../utils/storage";
import { createRefreshCoordinator, shouldClearFailedSession } from "./refreshCoordinator.mjs";
import type { TokenPairResponse } from "@/modules/identity/types/auth";

type RetriableRequestConfig = InternalAxiosRequestConfig & {
  _primeerpRetry?: boolean;
};

const refreshCoordinator = createRefreshCoordinator();

async function refreshAccessToken(): Promise<string> {
  const refreshToken = storage.getRefreshToken();
  if (!refreshToken) {
    throw new Error("No refresh token is available.");
  }

  const response = await client.post<TokenPairResponse>(
    "/identity/refresh",
    { refresh_token: refreshToken },
  );

  // Do not resurrect a session after logout or overwrite a newer login.
  if (storage.getRefreshToken() !== refreshToken) {
    throw new Error("The session changed while the token was refreshing.");
  }

  storage.setTokens(
    response.data.access_token,
    response.data.refresh_token,
  );
  return response.data.access_token;
}

client.interceptors.request.use((config) => {
  const token = storage.getAccessToken();
  const tenantId = storage.getTenantId();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  if (tenantId) config.headers["X-Tenant-ID"] = tenantId;
  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    const axiosError = error as {
      config?: RetriableRequestConfig;
      response?: { status?: number };
    };
    const config = axiosError.config;
    const url = config?.url ?? "";
    const isIdentitySessionRequest =
      url.includes("/identity/login") ||
      url.includes("/identity/refresh") ||
      url.includes("/identity/logout");

    if (
      axiosError.response?.status !== 401 ||
      !config ||
      config._primeerpRetry ||
      isIdentitySessionRequest
    ) {
      return Promise.reject(error);
    }

    config._primeerpRetry = true;
    let attemptedRefreshToken: string | null = null;

    try {
      const refreshAttempt = refreshCoordinator.run(
        () => storage.getRefreshToken(),
        refreshAccessToken,
      );
      attemptedRefreshToken = refreshAttempt.refreshTokenUsed;
      const accessToken = await refreshAttempt.promise;
      config.headers.Authorization = `Bearer ${accessToken}`;
      return await client.request(config);
    } catch (refreshError) {
      // Clear only the session snapshot that failed. This also clears an
      // access-token-only stale session, while preserving any newer login.
      if (shouldClearFailedSession(storage.getRefreshToken(), attemptedRefreshToken)) {
        storage.clear();
      }
      return Promise.reject(refreshError);
    }
  },
);

export default client;
