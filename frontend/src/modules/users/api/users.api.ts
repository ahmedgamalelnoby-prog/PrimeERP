import apiClient from "@/shared/api/client";

import type {
  ResetPasswordPayload,
  User,
  UserCreatePayload,
  UsersFilters,
  UsersPaginatedResponse,
  UserStatusPayload,
  UserUpdatePayload,
} from "../types/user";

const USERS_URL = "/identity/users";

export interface UserCompany {
  id: number;
  name: string;
  code: string | null;
}

export interface UserCompanyAccess {
  user_id: number;
  company_ids: number[];
  default_company_id: number | null;
}

function normalizeFilters(filters?: UsersFilters) {
  if (!filters) {
    return undefined;
  }

  return Object.fromEntries(
    Object.entries(filters).filter(
      ([, value]) =>
        value !== undefined &&
        value !== null &&
        value !== "",
    ),
  );
}

export const usersApi = {
  list(filters?: UsersFilters) {
  return apiClient.get<UsersPaginatedResponse>(
    `${USERS_URL}/`,
    {
      params: normalizeFilters(filters),
    },
  );
},

  getAvailableCompanies(userId: number) {
    return apiClient.get<UserCompany[]>(`${USERS_URL}/${userId}/companies/available`);
  },

  getCompanyAccess(userId: number) {
    return apiClient.get<UserCompanyAccess>(`${USERS_URL}/${userId}/companies`);
  },

  updateCompanyAccess(
    userId: number,
    payload: { company_ids: number[]; default_company_id: number },
  ) {
    return apiClient.put<UserCompanyAccess>(`${USERS_URL}/${userId}/companies`, payload);
  },

  get(id: number) {
    return apiClient.get<User>(`${USERS_URL}/${id}`);
  },

  create(payload: UserCreatePayload) {
    return apiClient.post<User>(`${USERS_URL}/`, payload);
  },

  update(
    id: number,
    payload: UserUpdatePayload,
  ) {
    return apiClient.put<User>(
      `${USERS_URL}/${id}`,
      payload,
    );
  },

  changeStatus(
    id: number,
    payload: UserStatusPayload,
  ) {
    return apiClient.patch<User>(
      `${USERS_URL}/${id}/status`,
      payload,
    );
  },

  resetPassword(
    id: number,
    payload: ResetPasswordPayload,
  ) {
    return apiClient.post<User>(
      `${USERS_URL}/${id}/reset-password`,
      payload,
    );
  },

  remove(id: number) {
    return apiClient.delete(
      `${USERS_URL}/${id}`,
    );
  },

  restore(id: number) {
    return apiClient.post<User>(
      `${USERS_URL}/${id}/restore`,
    );
  },
};