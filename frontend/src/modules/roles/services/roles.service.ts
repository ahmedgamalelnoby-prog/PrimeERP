import { rolesApi } from "../api/roles.api";

import type { Permission } from "../types/permission";
import type {
  Role,
  RoleCreatePayload,
  RolesFilters,
  RoleStatusPayload,
  RoleUpdatePayload,
} from "../types/role";

export const rolesService = {
  getRoles(filters?: RolesFilters): Promise<Role[]> {
    return rolesApi.list(filters);
  },

  getRole(id: number): Promise<Role> {
    return rolesApi.get(id);
  },

  createRole(
    payload: RoleCreatePayload,
  ): Promise<Role> {
    return rolesApi.create(payload);
  },

  updateRole(
    id: number,
    payload: RoleUpdatePayload,
  ): Promise<Role> {
    return rolesApi.update(id, payload);
  },

  changeStatus(
    id: number,
    payload: RoleStatusPayload,
  ): Promise<Role> {
    return rolesApi.changeStatus(id, payload);
  },

  updatePermissions(
    id: number,
    permissionIds: number[],
  ): Promise<Role> {
    return rolesApi.updatePermissions(
      id,
      permissionIds,
    );
  },

  deleteRole(id: number): Promise<void> {
    return rolesApi.remove(id);
  },

  getPermissions(): Promise<Permission[]> {
    return rolesApi.listPermissions();
  },
};