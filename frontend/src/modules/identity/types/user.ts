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
  permissions: string[];
}
