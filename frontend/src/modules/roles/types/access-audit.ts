export interface RoleAccessAuditUsage {
  global_users_active: number;
  global_users_inactive: number;
  company_memberships_active: number;
  company_memberships_inactive: number;
  branch_memberships_active: number;
  branch_memberships_inactive: number;
}

export interface RoleAccessAuditRole {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  permission_count: number;
  active_permission_count: number;
  inactive_permission_count: number;
  usage: RoleAccessAuditUsage;
}

export interface RoleAccessAuditPermission {
  id: number;
  name: string;
  resource: string;
  action: string;
  description: string | null;
}

export interface RoleAccessAuditFinding {
  code: string;
  severity: "warning" | "info";
  role_id?: number;
  role_name?: string;
  permission_id?: number;
  permission_name?: string;
  module_name?: string;
  count: number;
}

export interface ManifestPermissionGap {
  module_name: string;
  permission_name: string;
}

export interface RoleAccessAudit {
  summary: {
    roles_total: number;
    roles_active: number;
    permissions_total: number;
    permissions_active: number;
    permissions_without_active_role: number;
    manifest_permissions_declared: number;
    manifest_permissions_registered: number;
    manifest_permissions_missing: number;
    findings_total: number;
  };
  roles: RoleAccessAuditRole[];
  permissions_without_active_role: RoleAccessAuditPermission[];
  manifest_permissions_missing: ManifestPermissionGap[];
  findings: RoleAccessAuditFinding[];
}
