import client from "../../../shared/api/interceptors";
import { ENDPOINTS } from "../../../shared/api/endpoints";

import type {
  LoginPayload,
  LoginResponse,
  RefreshTokenPayload,
  TokenPairResponse,
} from "../types/auth";

import type { AuthenticatedUser } from "../types/user";

export const authApi = {
  login(payload: LoginPayload) {
    return client.post<LoginResponse>(
      ENDPOINTS.identity.login,
      payload
    );
  },

  refresh(payload: RefreshTokenPayload) {
    return client.post<TokenPairResponse>(
      ENDPOINTS.identity.refresh,
      payload
    );
  },

  getMe() {
    return client.get<AuthenticatedUser>(
      ENDPOINTS.identity.me
    );
  },
};