import apiClient from "@/shared/api/client";

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
