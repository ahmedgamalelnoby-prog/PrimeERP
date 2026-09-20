const API_BASE_URL = (import.meta.env.VITE_API_URL || "/api/v1").replace(/\/$/, "");

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(API_BASE_URL + path, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {}),
    },
    ...init,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload?.detail || "Request failed");
  return payload as T;
}
