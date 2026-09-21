import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import env from "../config/env";
import { storage } from "../utils/storage";

const client = axios.create({
  baseURL: env.API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = storage.getRefreshToken();
  if (!refreshToken) return null;

  if (!refreshPromise) {
    refreshPromise = axios
      .post<{ access_token: string; refresh_token: string }>(
        `${env.API_BASE_URL}/identity/refresh`,
        { refresh_token: refreshToken },
        { headers: { "Content-Type": "application/json", Accept: "application/json" }, timeout: 30000 },
      )
      .then((response) => {
        storage.setTokens(response.data.access_token, response.data.refresh_token);
        return response.data.access_token;
      })
      .catch(() => {
        storage.clear();
        return null;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = storage.getAccessToken();
  if (token && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    const status = error.response?.status;
    const url = original?.url ?? "";

    const isAuthEndpoint =
      url.includes("/identity/login") ||
      url.includes("/identity/refresh") ||
      url.includes("/identity/logout");

    if (status !== 401 || !original || original._retry || isAuthEndpoint) {
      return Promise.reject(error);
    }

    original._retry = true;
    const accessToken = await refreshAccessToken();

    if (!accessToken) {
      if (typeof window !== "undefined" && window.location.pathname !== "/login") {
        window.location.assign("/login");
      }
      return Promise.reject(error);
    }

    original.headers.Authorization = `Bearer ${accessToken}`;
    return client(original);
  },
);

export default client;
