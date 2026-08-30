import apiClient from "@/shared/api/client";

import type { Permission } from "../types/permission";
import type {
  Role,
  RoleCreatePayload,
  RolesFilters,
  RoleStatusPayload,
  RoleUpdatePayload,
} from "../types/role";

const BASE_URL = "/identity/roles";

function cleanParams(filters?: RolesFilters) {
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

export const rolesApi = {
  async list(filters?: RolesFilters): Promise<Role[]> {
    const response = await apiClient.get<Role[]>(
      `${BASE_URL}/`,
      {
        params: cleanParams(filters),
      },
    );

    return response.data;
  },

  async get(id: number): Promise<Role> {
    const response = await apiClient.get<Role>(
      `${BASE_URL}/${id}`,
    );

    return response.data;
  },

  async create(
    payload: RoleCreatePayload,
  ): Promise<Role> {
    const response = await apiClient.post<Role>(
      `${BASE_URL}/`,
      payload,
    );

    return response.data;
  },

  async update(
    id: number,
    payload: RoleUpdatePayload,
  ): Promise<Role> {
    const response = await apiClient.put<Role>(
      `${BASE_URL}/${id}`,
      payload,
    );

    return response.data;
  },

  async changeStatus(
    id: number,
    payload: RoleStatusPayload,
  ): Promise<Role> {
    const response = await apiClient.post<Role>(
      `${BASE_URL}/${id}/status`,
      payload,
    );

    return response.data;
  },

  async updatePermissions(
    id: number,
    permissionIds: number[],
  ): Promise<Role> {
    const response = await apiClient.put<Role>(
      `${BASE_URL}/${id}/permissions`,
      {
        permission_ids: permissionIds,
      },
    );

    return response.data;
  },

  async remove(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}/${id}`);
  },

  async listPermissions(): Promise<Permission[]> {
    const response = await apiClient.get<Permission[]>(
      `${BASE_URL}/permissions/`,
    );

    return response.data;
  },
};