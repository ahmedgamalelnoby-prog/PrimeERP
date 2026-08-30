import { usersApi } from "../api/users.api";

import type {
  ResetPasswordPayload,
  User,
  UserCreatePayload,
  UsersFilters,
  UsersPaginatedResponse,
  UserStatusPayload,
  UserUpdatePayload,
} from "../types/user";

export const usersService = {
  async getAll(
  filters?: UsersFilters,
): Promise<UsersPaginatedResponse> {
  const response = await usersApi.list(filters);

  return response.data;
},

  async getById(
    id: number,
  ): Promise<User> {
    const response =
      await usersApi.get(id);

    return response.data;
  },

  async create(
    payload: UserCreatePayload,
  ): Promise<User> {
    const response =
      await usersApi.create(payload);

    return response.data;
  },

  async update(
    id: number,
    payload: UserUpdatePayload,
  ): Promise<User> {
    const response =
      await usersApi.update(
        id,
        payload,
      );

    return response.data;
  },

  async changeStatus(
    id: number,
    payload: UserStatusPayload,
  ): Promise<User> {
    const response =
      await usersApi.changeStatus(
        id,
        payload,
      );

    return response.data;
  },

  async resetPassword(
    id: number,
    payload: ResetPasswordPayload,
  ): Promise<User> {
    const response =
      await usersApi.resetPassword(
        id,
        payload,
      );

    return response.data;
  },

  async remove(
    id: number,
  ): Promise<void> {
    await usersApi.remove(id);
  },

  async restore(
    id: number,
  ): Promise<User> {
    const response =
      await usersApi.restore(id);

    return response.data;
  },
};