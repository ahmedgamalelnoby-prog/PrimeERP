import client from "@/shared/api/client";
import { storage } from "@/shared/utils/storage";

export interface LoginRequest {
  login: string;
  password: string;
  tenant_slug?: string | null;
  tenant_name?: string | null;
}

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

export interface AuthenticatedUser {
  id: number;
  tenant_id: number | null;
  username: string;
  email: string;
  full_name: string | null;
  role_id: number | null;
  is_active: boolean;
  is_superuser: boolean;
  is_platform_admin: boolean;
  preferred_language: string | null;
  tenant_slug: string | null;
  tenant_name: string | null;
  tenant_status: string | null;
  subscription_status: string | null;
  enabled_modules: string[];
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: AuthenticatedUser;
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

  const response =
    await client.post<RegisterResponse>(
      "/identity/register",
      requestPayload,
    );

  return response.data;
}

async function login(
  payload: LoginRequest,
): Promise<LoginResponse> {
  const loginValue = payload.login.trim();

  if (!loginValue) {
    throw new Error(
      "Username or email is required.",
    );
  }

  if (!payload.password) {
    throw new Error(
      "Password is required.",
    );
  }

  const tenantSlug = payload.tenant_slug?.trim() || null;
  const tenantName = payload.tenant_name?.trim() || null;

  const requestPayload: LoginRequest = {
    login: loginValue,
    password: payload.password,
    tenant_slug: tenantSlug,
    tenant_name: tenantName,
  };

  const response =
    await client.post<LoginResponse>(
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
  storage.clear();
}

async function getCurrentUser(): Promise<AuthenticatedUser> {
  const response =
    await client.get<AuthenticatedUser>(
      "/identity/me",
    );

  return response.data;
}

export const authService = {
  register,
  login,
  logout,
  getCurrentUser,
};