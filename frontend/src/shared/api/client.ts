import axios from "axios";

import env from "../config/env";
import { storage } from "../utils/storage";

const client = axios.create({
  baseURL: env.API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

client.interceptors.request.use((config) => {
  const tenantId = storage.getTenantId();
  const companyId = localStorage.getItem("company_id");
  if (tenantId) config.headers["X-Tenant-ID"] = tenantId;
  if (companyId) config.headers["X-Company-ID"] = companyId;
  return config;
});

export default client;
