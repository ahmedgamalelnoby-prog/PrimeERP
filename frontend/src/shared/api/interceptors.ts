import client from "./client";
import { storage } from "../utils/storage";

client.interceptors.request.use((config) => {
  const token = storage.getAccessToken();
  const tenantId = storage.getTenantId();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  if (tenantId) config.headers["X-Tenant-ID"] = tenantId;
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) storage.clear();
    return Promise.reject(error);
  },
);

export default client;
