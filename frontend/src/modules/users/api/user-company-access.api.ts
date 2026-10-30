import apiClient from "@/shared/api/client";

export interface CompanyAccessAuditBranch {
  id: number;
  name: string;
  code: string | null;
  is_active: boolean;
}

export interface CompanyAccessAuditBranchGrant {
  branch_id: number;
  membership_is_active: boolean | null;
  role_id: number | null;
  role_name: string | null;
}

export interface CompanyAccessAuditMember {
  user_id: number;
  username: string;
  full_name: string | null;
  user_is_active: boolean;
  company_membership_is_active: boolean | null;
  company_role_id: number | null;
  company_role_name: string | null;
  branch_access: CompanyAccessAuditBranchGrant[];
}

export interface CompanyAccessAudit {
  company_id: number;
  company_name: string;
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  branches: CompanyAccessAuditBranch[];
  items: CompanyAccessAuditMember[];
}

export interface AccessibleCompany {
  id: number;
  name: string;
  code: string | null;
}

export interface CompanyMember {
  user_id: number;
  username: string;
  full_name: string | null;
  user_is_active: boolean;
  membership_is_active: boolean;
  role_id: number | null;
}

export interface AccessibleBranch {
  id: number;
  company_id: number;
  name: string;
  code: string | null;
}

export interface BranchMember {
  user_id: number;
  username: string;
  full_name: string | null;
  user_is_active: boolean;
  membership_is_active: boolean;
  role_id: number | null;
}

export interface AssignableCompanyRole {
  id: number;
  name: string;
  description: string | null;
}

function companyConfig(companyId: number) {
  return {
    headers: {
      "X-Company-ID": String(companyId),
      "X-Branch-ID": "",
    },
  };
}

export const userCompanyAccessApi = {
  async getCompanies() {
    const response = await apiClient.get<AccessibleCompany[]>("/companies/accessible", {
      headers: { "X-Branch-ID": "" },
    });
    return response.data;
  },

  async getBranches(companyId: number) {
    const response = await apiClient.get<AccessibleBranch[]>("/branches", {
      ...companyConfig(companyId),
      params: { company_id: companyId, active_only: true },
    });
    return response.data;
  },

  async getBranchMembers(companyId: number, branchId: number) {
    const response = await apiClient.get<BranchMember[]>(
      `/branches/${branchId}/members`,
      companyConfig(companyId),
    );
    return response.data;
  },

  async getAssignableBranchRoles(companyId: number, branchId: number) {
    const response = await apiClient.get<AssignableCompanyRole[]>(
      `/branches/${branchId}/assignable-roles`,
      companyConfig(companyId),
    );
    return response.data;
  },

  async grantBranch(companyId: number, branchId: number, userId: number, roleId: number | null) {
    await apiClient.put(
      `/branches/${branchId}/members/${userId}`,
      null,
      {
        ...companyConfig(companyId),
        params: roleId ? { role_id: roleId } : undefined,
      },
    );
  },

  async revokeBranch(companyId: number, branchId: number, userId: number) {
    await apiClient.delete(
      `/branches/${branchId}/members/${userId}`,
      companyConfig(companyId),
    );
  },

  async clearBranchRole(companyId: number, branchId: number, userId: number) {
    await apiClient.delete(
      `/branches/${branchId}/members/${userId}/role`,
      companyConfig(companyId),
    );
  },

  async getAccessAudit(companyId: number, page = 1, pageSize = 50) {
    const response = await apiClient.get<CompanyAccessAudit>(
      `/companies/${companyId}/membership-audit`,
      {
        ...companyConfig(companyId),
        params: { page, page_size: pageSize },
      },
    );
    return response.data;
  },

  async getMembers(companyId: number) {
    const response = await apiClient.get<CompanyMember[]>(
      `/companies/${companyId}/members`,
      companyConfig(companyId),
    );
    return response.data;
  },

  async getAssignableRoles(companyId: number) {
    const response = await apiClient.get<AssignableCompanyRole[]>(
      `/companies/${companyId}/assignable-roles`,
      companyConfig(companyId),
    );
    return response.data;
  },

  async grant(companyId: number, userId: number, roleId: number | null) {
    await apiClient.put(
      `/companies/${companyId}/members/${userId}`,
      null,
      {
        ...companyConfig(companyId),
        params: roleId ? { role_id: roleId } : undefined,
      },
    );
  },

  async revoke(companyId: number, userId: number) {
    await apiClient.delete(
      `/companies/${companyId}/members/${userId}`,
      companyConfig(companyId),
    );
  },

  async clearRole(companyId: number, userId: number) {
    await apiClient.delete(
      `/companies/${companyId}/members/${userId}/role`,
      companyConfig(companyId),
    );
  },
};
