import { STORAGE_KEYS } from "../constants/storage";

export const storage = {
  getAccessToken() { return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN); },
  setAccessToken(access: string) { localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, access); },
  getRefreshToken() { return localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN); },
  setTokens(access: string, refresh: string) {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, access);
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refresh);
  },
  getTenantId() { return localStorage.getItem(STORAGE_KEYS.TENANT_ID); },
  setTenantId(tenantId: number | null | undefined) {
    const current = localStorage.getItem(STORAGE_KEYS.TENANT_ID);
    const next = tenantId && tenantId > 0 ? String(tenantId) : null;
    if (current !== next) {
      localStorage.removeItem(STORAGE_KEYS.COMPANY_ID);
      localStorage.removeItem(STORAGE_KEYS.BRANCH_ID);
    }
    if (next) localStorage.setItem(STORAGE_KEYS.TENANT_ID, next);
    else localStorage.removeItem(STORAGE_KEYS.TENANT_ID);
  },
  getCompanyId() { return localStorage.getItem(STORAGE_KEYS.COMPANY_ID); },
  setCompanyId(companyId: number | string | null | undefined) {
    const value = Number(companyId);
    if (Number.isInteger(value) && value > 0) localStorage.setItem(STORAGE_KEYS.COMPANY_ID, String(value));
    else localStorage.removeItem(STORAGE_KEYS.COMPANY_ID);
  },
  getBranchId() { return localStorage.getItem(STORAGE_KEYS.BRANCH_ID); },
  setBranchId(branchId: number | string | null | undefined) {
    const value = Number(branchId);
    if (Number.isInteger(value) && value > 0) localStorage.setItem(STORAGE_KEYS.BRANCH_ID, String(value));
    else localStorage.removeItem(STORAGE_KEYS.BRANCH_ID);
  },
  clearBranchContext() { localStorage.removeItem(STORAGE_KEYS.BRANCH_ID); },
  clearCompanyContext() {
    localStorage.removeItem(STORAGE_KEYS.COMPANY_ID);
    localStorage.removeItem(STORAGE_KEYS.BRANCH_ID);
  },
  clear() {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.TENANT_ID);
    localStorage.removeItem(STORAGE_KEYS.COMPANY_ID);
    localStorage.removeItem(STORAGE_KEYS.BRANCH_ID);
  },
};
