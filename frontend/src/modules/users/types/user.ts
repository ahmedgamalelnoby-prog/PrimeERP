export interface User {
  id: number;
  tenant_id: number | null;

  username: string;
  email: string;

  full_name: string | null;
  phone: string | null;
  address: string | null;
  profile_image: string | null;
  preferred_language: string | null;

  is_active: boolean;
  is_superuser: boolean;
  is_platform_admin: boolean;
  is_deleted: boolean;
  must_change_password: boolean;

  role_id: number | null;
  role_name: string | null;

  last_login: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface UserCreatePayload {
  username: string;
  email: string;
  password: string;

  tenant_id?: number | null;

  full_name?: string;
  phone?: string;
  address?: string;
  profile_image?: string;
  preferred_language?: string;

  role_id?: number | null;

  is_active: boolean;
  is_superuser: boolean;
  is_platform_admin?: boolean;
  must_change_password: boolean;
}

export interface UserUpdatePayload {
  username?: string;
  email?: string;
  password?: string;

  tenant_id?: number | null;

  full_name?: string;
  phone?: string;
  address?: string;
  profile_image?: string;
  preferred_language?: string;

  role_id?: number | null;

  is_active?: boolean;
  is_superuser?: boolean;
  is_platform_admin?: boolean;
  must_change_password?: boolean;
}

export interface UserStatusPayload {
  is_active: boolean;
}

export interface ResetPasswordPayload {
  new_password: string;
  must_change_password: boolean;
}

export interface UsersFilters {
  search?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export interface PageMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface UsersPaginatedResponse {
  items: User[];
  meta: PageMeta;
}