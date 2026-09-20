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
    if (tenantId && tenantId > 0) localStorage.setItem(STORAGE_KEYS.TENANT_ID, String(tenantId));
    else localStorage.removeItem(STORAGE_KEYS.TENANT_ID);
  },
  clear() {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.TENANT_ID);
  },
};
