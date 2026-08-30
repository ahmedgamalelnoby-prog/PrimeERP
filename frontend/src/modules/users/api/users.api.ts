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