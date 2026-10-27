import type { AuthenticatedUser } from "./user";

export interface LoginPayload {
  login: string;
  password: string;
  tenant_slug?: string | null;
  tenant_name?: string | null;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: AuthenticatedUser;
}

export interface RefreshTokenPayload {
  refresh_token: string;
}

export interface TokenPairResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}
