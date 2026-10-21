import axios from "axios";
import env from "../config/env";
import { storage } from "../utils/storage";

const client = axios.create({
  baseURL: env.API_BASE_URL,
  timeout: 30000,
  headers: { "Content-Type": "application/json", Accept: "application/json" },
});

client.interceptors.request.use((config) => {
  const token = storage.getAccessToken();
  if (token) config.headers.Authorization = "Bearer " + token;
  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error?.response?.status === 401) storage.clear();
    return Promise.reject(error);
  },
);

export default client;
