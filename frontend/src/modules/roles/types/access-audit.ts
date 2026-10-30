export interface RoleAccessAuditUsage {
  global_users: number;
  company_memberships: number;
  branch_memberships: number;
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
  count: number;
}

export interface RoleAccessAudit {
  summary: {
    roles_total: number;
    roles_active: number;
    permissions_total: number;
    permissions_active: number;
    permissions_without_active_role: number;
    findings_total: number;
  };
  roles: RoleAccessAuditRole[];
  permissions_without_active_role: RoleAccessAuditPermission[];
  findings: RoleAccessAuditFinding[];
}
