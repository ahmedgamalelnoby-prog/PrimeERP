import apiClient from "./api/interceptors";

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await apiClient.request<T>({
    url: path,
    method: init.method || "GET",
    headers: init.headers ? Object.fromEntries(new Headers(init.headers).entries()) : undefined,
    data: init.body,
  });
  return response.data;
}
