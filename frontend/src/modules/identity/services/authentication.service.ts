import client from "@/shared/api/client";
import { storage } from "@/shared/utils/storage";

import type { LoginPayload, LoginResponse } from "../types/auth";
import type { AuthenticatedUser } from "../types/user";

export type LoginRequest = LoginPayload;

async function login(payload: LoginPayload): Promise<LoginResponse> {
  const loginValue = payload.login.trim();

  if (!loginValue) {
    throw new Error("Username or email is required.");
  }

  if (!payload.password) {
    throw new Error("Password is required.");
  }

  const requestPayload: LoginPayload = {
    login: loginValue,
    password: payload.password,
    tenant_slug: payload.tenant_slug?.trim() || null,
    tenant_name: payload.tenant_name?.trim() || null,
  };

  const response = await client.post<LoginResponse>(
    "/identity/login",
    requestPayload,
  );

  storage.setTokens(
    response.data.access_token,
    response.data.refresh_token,
  );
  storage.setTenantId(response.data.user.tenant_id);

  return response.data;
}

async function logout(): Promise<void> {
  const refreshToken = storage.getRefreshToken();
  storage.clear();

  if (!refreshToken) return;

  try {
    await client.post("/identity/logout", {
      refresh_token: refreshToken,
    });
  } catch {
    // The local session is already cleared; server-side expiry remains the fallback.
  }
}

async function getCurrentUser(): Promise<AuthenticatedUser> {
  const response = await client.get<AuthenticatedUser>("/identity/me");
  return response.data;
}

export const authService = {
  login,
  logout,
  getCurrentUser,
};
