import client from "@/shared/api/client";
import { storage } from "@/shared/utils/storage";

import type { LoginPayload, LoginResponse } from "../types/auth";
import type { AuthenticatedUser } from "../types/user";

export type LoginRequest = LoginPayload;

export interface RegisterRequest {
  business_name: string;
  owner_name: string;
  username: string;
  email: string;
  mobile: string;
  password: string;
}

export interface RegisterResponse {
  success: boolean;
  message: string;
  tenant_id?: number;
  user_id?: number;
  tenant_slug?: string;
}

async function register(
  payload: RegisterRequest,
): Promise<RegisterResponse> {
  const requestPayload: RegisterRequest = {
    business_name: payload.business_name.trim(),
    owner_name: payload.owner_name.trim(),
    username: payload.username.trim(),
    email: payload.email.trim().toLowerCase(),
    mobile: payload.mobile.trim(),
    password: payload.password,
  };

  const response = await client.post<RegisterResponse>(
    "/identity/register",
    requestPayload,
  );

  return response.data;
}

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

  try {
    if (refreshToken) {
      await client.post("/identity/logout", {
        refresh_token: refreshToken,
      });
    }
  } finally {
    storage.clear();
  }
}

async function getCurrentUser(): Promise<AuthenticatedUser> {
  const response = await client.get<AuthenticatedUser>("/identity/me");
  return response.data;
}

export const authService = {
  register,
  login,
  logout,
  getCurrentUser,
};
