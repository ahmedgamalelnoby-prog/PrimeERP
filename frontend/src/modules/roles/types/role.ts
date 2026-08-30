import type { Permission } from "./permission";

export interface Role {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  permissions: Permission[];
  users_count: number;
  created_at: string;
  updated_at: string | null;
}

export interface RoleCreatePayload {
  name: string;
  description?: string | null;
  is_active: boolean;
  permission_ids: number[];
}

export interface RoleUpdatePayload {
  name?: string;
  description?: string | null;
  is_active?: boolean;
  permission_ids?: number[];
}

export interface RoleStatusPayload {
  is_active: boolean;
}

export interface RolesFilters {
  search?: string;
  is_active?: boolean;
}